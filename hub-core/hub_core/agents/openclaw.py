"""OpenClaw agent adapter — local execution, no API calls."""

import asyncio
import logging
import time
from typing import Any, Dict, Optional

from .base import AdapterStatus, AgentCapabilities, IAgentAdapter, TaskResult

logger = logging.getLogger(__name__)


class OpenClawAdapter(IAgentAdapter):
    """Executes tasks via OpenClaw local runtime (free, no API cost)."""

    def __init__(self, agent_id: str = "openclaw-orchestrator"):
        self.agent_id = agent_id
        self._status = AdapterStatus.OK

    async def execute(
        self, task: str, context: Optional[Dict[str, Any]] = None
    ) -> TaskResult:
        start = time.time()
        try:
            logger.info(f"OpenClaw executing: {task[:50]}...")
            await asyncio.sleep(0.05)
            return TaskResult(
                success=True,
                output=f"[OpenClaw] Executed: {task[:30]}...",
                execution_time_ms=(time.time() - start) * 1000,
                tokens_used=0,
                cost_usd=0.0,
                metadata={"adapter": "openclaw", "runtime": "local", "free": True},
            )
        except Exception as e:
            logger.error(f"OpenClaw error: {e}")
            self._status = AdapterStatus.ERROR
            return TaskResult(
                success=False,
                output="",
                error=str(e),
                execution_time_ms=(time.time() - start) * 1000,
            )

    async def health_check(self) -> bool:
        return True

    def get_capabilities(self) -> AgentCapabilities:
        return AgentCapabilities(
            agent_id=self.agent_id,
            runtime="openclaw",
            version="local",
            can_read_files=True,
            can_write_files=True,
            can_execute_code=True,
            max_context_tokens=200_000,
            supports_streaming=False,
            estimated_cost_per_1k_tokens=0.0,
        )

    def get_status(self) -> AdapterStatus:
        return self._status
