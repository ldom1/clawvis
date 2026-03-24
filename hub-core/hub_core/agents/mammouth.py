"""MammouthAI adapters — unified API gateway for Claude, Gemini, Mistral, and more.

MammouthAI acts like OpenRouter: single endpoint, multiple providers.
Includes both a fixed-model adapter and a dynamic model-selection adapter.
"""

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

from .base import IAgentAdapter, TaskResult, AgentCapabilities, AdapterStatus

logger = logging.getLogger(__name__)

API_BASE = "https://api.mammouth.ai/v1"

# Model catalog: cost per 1K tokens (input, output), quality/speed scores
MAMMOUTH_MODELS: Dict[str, Dict] = {
    # OpenAI
    "gpt-5.2-pro": {
        "provider": "OpenAI",
        "cost_per_1k": {"input": 0.80, "output": 4.00},
        "speed": 3,
        "quality": 5,
        "context": 128000,
        "tags": ["reasoning", "quality"],
    },
    "gpt-5.2": {
        "provider": "OpenAI",
        "cost_per_1k": {"input": 0.10, "output": 0.40},
        "speed": 4,
        "quality": 5,
        "context": 128000,
        "tags": ["balanced", "code"],
    },
    "gpt-5.1": {
        "provider": "OpenAI",
        "cost_per_1k": {"input": 0.05, "output": 0.20},
        "speed": 4,
        "quality": 4,
        "context": 128000,
        "tags": ["balanced"],
    },
    "gpt-5-mini": {
        "provider": "OpenAI",
        "cost_per_1k": {"input": 0.005, "output": 0.015},
        "speed": 5,
        "quality": 4,
        "context": 128000,
        "tags": ["fast", "cheap"],
    },
    "gpt-5-nano": {
        "provider": "OpenAI",
        "cost_per_1k": {"input": 0.001, "output": 0.005},
        "speed": 5,
        "quality": 3,
        "context": 128000,
        "tags": ["ultra-cheap"],
    },
    "gpt-5.2-codex": {
        "provider": "OpenAI",
        "cost_per_1k": {"input": 0.10, "output": 0.40},
        "speed": 4,
        "quality": 5,
        "context": 128000,
        "tags": ["code"],
    },
    # Anthropic
    "claude-opus-4-6": {
        "provider": "Anthropic",
        "cost_per_1k": {"input": 3.00, "output": 15.00},
        "speed": 2,
        "quality": 5,
        "context": 1000000,
        "tags": ["reasoning", "quality"],
    },
    "claude-sonnet-4-6": {
        "provider": "Anthropic",
        "cost_per_1k": {"input": 0.30, "output": 1.50},
        "speed": 4,
        "quality": 5,
        "context": 1000000,
        "tags": ["balanced"],
    },
    "claude-haiku-4-5": {
        "provider": "Anthropic",
        "cost_per_1k": {"input": 0.03, "output": 0.10},
        "speed": 5,
        "quality": 4,
        "context": 200000,
        "tags": ["fast"],
    },
    # Google
    "gemini-3.1-pro-preview": {
        "provider": "Google",
        "cost_per_1k": {"input": 0.075, "output": 0.30},
        "speed": 4,
        "quality": 5,
        "context": 1000000,
        "tags": ["reasoning", "multimodal"],
    },
    "gemini-3-flash-preview": {
        "provider": "Google",
        "cost_per_1k": {"input": 0.01, "output": 0.04},
        "speed": 5,
        "quality": 4,
        "context": 1000000,
        "tags": ["fast", "cheap", "translation"],
    },
    "gemini-2.5-pro": {
        "provider": "Google",
        "cost_per_1k": {"input": 0.075, "output": 0.30},
        "speed": 4,
        "quality": 4,
        "context": 1000000,
        "tags": ["analysis"],
    },
    # Mistral
    "mistral-large-3": {
        "provider": "Mistral AI",
        "cost_per_1k": {"input": 0.15, "output": 0.45},
        "speed": 4,
        "quality": 4,
        "context": 128000,
        "tags": ["code", "multilingual"],
    },
    "mistral-small-3.2-24b-instruct": {
        "provider": "Mistral AI",
        "cost_per_1k": {"input": 0.02, "output": 0.06},
        "speed": 5,
        "quality": 4,
        "context": 32000,
        "tags": ["cheap"],
    },
    # DeepSeek
    "deepseek-r1-0528": {
        "provider": "DeepSeek",
        "cost_per_1k": {"input": 0.05, "output": 0.20},
        "speed": 3,
        "quality": 5,
        "context": 128000,
        "tags": ["reasoning", "math"],
    },
    # Meta
    "llama-4-maverick": {
        "provider": "Meta",
        "cost_per_1k": {"input": 0.05, "output": 0.20},
        "speed": 4,
        "quality": 4,
        "context": 128000,
        "tags": ["general"],
    },
    "llama-4-scout": {
        "provider": "Meta",
        "cost_per_1k": {"input": 0.01, "output": 0.04},
        "speed": 5,
        "quality": 3,
        "context": 128000,
        "tags": ["ultra-cheap"],
    },
    # Others
    "qwen3-coder-plus": {
        "provider": "Alibaba",
        "cost_per_1k": {"input": 0.10, "output": 0.40},
        "speed": 4,
        "quality": 5,
        "context": 997000,
        "tags": ["code"],
    },
}

_TASK_MODELS = {
    "translation": ["gemini-3-flash-preview", "mistral-small-3.2-24b-instruct"],
    "code": ["qwen3-coder-plus", "gpt-5.2-codex", "mistral-large-3"],
    "reasoning": ["claude-opus-4-6", "gpt-5.2-pro", "deepseek-r1-0528"],
    "fast": ["gpt-5-mini", "gemini-3-flash-preview"],
    "general": ["gpt-5.2", "claude-sonnet-4-6", "mistral-large-3"],
}

_BUDGET_MODELS = {
    "unlimited": ["gpt-5.2-pro", "claude-opus-4-6"],
    "medium": ["gpt-5.2", "claude-sonnet-4-6", "mistral-large-3"],
    "budget": [
        "gpt-5-mini",
        "gemini-3-flash-preview",
        "mistral-small-3.2-24b-instruct",
    ],
    "ultra-cheap": ["gpt-5-nano", "llama-4-scout"],
}


async def _post(
    api_key: str, model: str, messages: list, max_tokens: int = 1000
) -> dict:
    """Shared HTTP call to MammouthAI chat/completions."""
    import aiohttp

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{API_BASE}/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
            timeout=aiohttp.ClientTimeout(total=30),
        ) as resp:
            if resp.status != 200:
                raise RuntimeError(f"API {resp.status}: {await resp.text()}")
            return await resp.json()


class MammouthAIAdapter(IAgentAdapter):
    """Fixed-model adapter using MammouthAI unified API gateway."""

    def __init__(self, agent_id: str, model: str, api_key: Optional[str] = None):
        self.agent_id = agent_id
        self.model = model
        self._api_key = api_key or os.getenv("MAMMOUTH_API_KEY")
        self._status = AdapterStatus.OK
        if not self._api_key:
            raise ValueError("MAMMOUTH_API_KEY not found")

    def _cost(self, input_tokens: int, output_tokens: int) -> float:
        cfg = MAMMOUTH_MODELS.get(self.model, {}).get(
            "cost_per_1k", {"input": 0, "output": 0}
        )
        return (input_tokens / 1000) * cfg["input"] + (output_tokens / 1000) * cfg[
            "output"
        ]

    async def execute(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        start = time.time()
        content = task
        if context:
            ctx = "\n\n".join(
                f"[{k}]: {json.dumps(v) if not isinstance(v, str) else v}"
                for k, v in context.items()
            )
            content = f"{task}\n\n[Context]:\n{ctx}"
        try:
            data = await _post(
                self._api_key, self.model, [{"role": "user", "content": content}]
            )
            usage = data.get("usage", {})
            in_tok = usage.get("prompt_tokens", 0)
            out_tok = usage.get("completion_tokens", 0)
            cost = self._cost(in_tok, out_tok)
            logger.info(f"{self.agent_id}: {in_tok + out_tok} tokens, ${cost:.4f}")
            return TaskResult(
                success=True,
                output=data["choices"][0]["message"]["content"],
                execution_time_ms=(time.time() - start) * 1000,
                tokens_used=in_tok + out_tok,
                cost_usd=cost,
                metadata={
                    "adapter": "mammouth",
                    "model": self.model,
                    "input_tokens": in_tok,
                    "output_tokens": out_tok,
                },
            )
        except Exception as e:
            logger.error(f"{self.agent_id} error: {e}")
            self._status = AdapterStatus.ERROR
            return TaskResult(
                success=False,
                output="",
                error=str(e),
                execution_time_ms=(time.time() - start) * 1000,
            )

    async def health_check(self) -> bool:
        try:
            import aiohttp

            async with aiohttp.ClientSession() as s:
                async with s.get(
                    f"{API_BASE}/models",
                    headers={"Authorization": f"Bearer {self._api_key}"},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as r:
                    return r.status == 200
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            self._status = AdapterStatus.DEGRADED
            return False

    def get_capabilities(self) -> AgentCapabilities:
        cfg = MAMMOUTH_MODELS.get(self.model, {})
        return AgentCapabilities(
            agent_id=self.agent_id,
            runtime=f"mammouth-{cfg.get('provider', 'unknown').lower()}",
            version=self.model,
            can_read_files=False,
            can_write_files=False,
            can_execute_code="code" in cfg.get("tags", []),
            max_context_tokens=cfg.get("context", 128000),
            supports_streaming=True,
            estimated_cost_per_1k_tokens=cfg.get("cost_per_1k", {}).get("output", 0),
        )

    def get_status(self) -> AdapterStatus:
        return self._status


class DynamicMammouthAdapter(IAgentAdapter):
    """Selects the best MammouthAI model based on task type and budget tier."""

    def __init__(
        self,
        agent_id: str = "dynamic-mammouth",
        task_type: str = "general",
        budget_tier: str = "medium",
        api_key: Optional[str] = None,
        preferred_models: Optional[List[str]] = None,
    ):
        self.agent_id = agent_id
        self.task_type = task_type
        self.budget_tier = budget_tier
        self._api_key = api_key or os.getenv("MAMMOUTH_API_KEY")
        self.preferred_models = preferred_models or []
        self._status = AdapterStatus.OK
        self._selected_model: Optional[str] = None
        if not self._api_key:
            raise ValueError("MAMMOUTH_API_KEY not found")

    def select_model(self) -> str:
        task_candidates = _TASK_MODELS.get(self.task_type, _TASK_MODELS["general"])
        budget_set = set(_BUDGET_MODELS.get(self.budget_tier, _BUDGET_MODELS["medium"]))
        candidates = [m for m in task_candidates if m in budget_set] or task_candidates[
            :1
        ]
        if self.preferred_models:
            candidates = [
                m for m in self.preferred_models if m in MAMMOUTH_MODELS
            ] + candidates
        self._selected_model = candidates[0]
        logger.info(
            f"Model selected: task={self.task_type}, budget={self.budget_tier} → {self._selected_model}"
        )
        return self._selected_model

    async def execute(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        start = time.time()
        model = self.select_model()
        cfg = MAMMOUTH_MODELS.get(model, {})
        content = task
        if context:
            ctx = "\n\n".join(
                f"[{k}]: {json.dumps(v) if not isinstance(v, str) else v}"
                for k, v in context.items()
            )
            content = f"{task}\n\n[Context]:\n{ctx}"
        try:
            data = await _post(
                self._api_key, model, [{"role": "user", "content": content}]
            )
            usage = data.get("usage", {})
            in_tok = usage.get("prompt_tokens", 0)
            out_tok = usage.get("completion_tokens", 0)
            cost_cfg = cfg.get("cost_per_1k", {"input": 0, "output": 0})
            cost = (in_tok / 1000) * cost_cfg["input"] + (out_tok / 1000) * cost_cfg[
                "output"
            ]
            return TaskResult(
                success=True,
                output=data["choices"][0]["message"]["content"],
                execution_time_ms=(time.time() - start) * 1000,
                tokens_used=in_tok + out_tok,
                cost_usd=cost,
                metadata={
                    "adapter": "dynamic-mammouth",
                    "model": model,
                    "provider": cfg.get("provider"),
                    "task_type": self.task_type,
                    "budget_tier": self.budget_tier,
                },
            )
        except Exception as e:
            logger.error(f"DynamicMammouth error: {e}")
            self._status = AdapterStatus.ERROR
            return TaskResult(
                success=False,
                output="",
                error=str(e),
                execution_time_ms=(time.time() - start) * 1000,
            )

    async def health_check(self) -> bool:
        adapter = MammouthAIAdapter(self.agent_id, self.select_model(), self._api_key)
        return await adapter.health_check()

    def get_capabilities(self) -> AgentCapabilities:
        if not self._selected_model:
            self.select_model()
        cfg = MAMMOUTH_MODELS.get(self._selected_model, {})
        return AgentCapabilities(
            agent_id=self.agent_id,
            runtime="mammouth-dynamic",
            version=self._selected_model or "unknown",
            can_execute_code="code" in cfg.get("tags", []),
            max_context_tokens=cfg.get("context", 128000),
            supports_streaming=True,
            estimated_cost_per_1k_tokens=cfg.get("cost_per_1k", {}).get("output", 0),
        )

    def get_status(self) -> AdapterStatus:
        return self._status


# Convenience subclasses for fixed models


class ClaudeAdapter(MammouthAIAdapter):
    def __init__(self, agent_id: str = "claude-sonnet-mammouth"):
        super().__init__(agent_id=agent_id, model="claude-sonnet-4-6")


class GeminiAdapter(MammouthAIAdapter):
    def __init__(self, agent_id: str = "gemini-flash-mammouth"):
        super().__init__(agent_id=agent_id, model="gemini-3-flash-preview")


class MistralAdapter(MammouthAIAdapter):
    def __init__(self, agent_id: str = "mistral-small-mammouth"):
        super().__init__(agent_id=agent_id, model="mistral-small-3.2-24b-instruct")
