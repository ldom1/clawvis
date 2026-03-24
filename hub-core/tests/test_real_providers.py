"""Integration tests for real MammouthAI provider calls.

Requires MAMMOUTH_API_KEY to be set. Skipped otherwise.

Usage:
  MAMMOUTH_API_KEY=sk-... uv run pytest tests/test_real_providers.py -v
"""

import os

import pytest

MAMMOUTH_API_KEY = os.getenv("MAMMOUTH_API_KEY")
pytestmark = pytest.mark.skipif(
    not MAMMOUTH_API_KEY,
    reason="MAMMOUTH_API_KEY not set — skipping real provider tests",
)


@pytest.mark.asyncio
async def test_claude_adapter_real():
    from hub_core.agents.mammouth import ClaudeAdapter

    adapter = ClaudeAdapter()
    result = await adapter.execute("Reply with the single word: OK")
    assert result.success, f"Failed: {result.error}"
    assert "OK" in result.output or len(result.output) > 0
    assert result.tokens_used > 0


@pytest.mark.asyncio
async def test_gemini_adapter_real():
    from hub_core.agents.mammouth import GeminiAdapter

    adapter = GeminiAdapter()
    result = await adapter.execute("Reply with the single word: OK")
    assert result.success, f"Failed: {result.error}"
    assert result.tokens_used > 0


@pytest.mark.asyncio
async def test_mistral_adapter_real():
    from hub_core.agents.mammouth import MistralAdapter

    adapter = MistralAdapter()
    result = await adapter.execute("Reply with the single word: OK")
    assert result.success, f"Failed: {result.error}"
    assert result.tokens_used > 0


@pytest.mark.asyncio
async def test_dynamic_adapter_real():
    from hub_core.agents.mammouth import DynamicMammouthAdapter

    adapter = DynamicMammouthAdapter(task_type="general", budget_tier="budget")
    result = await adapter.execute("Reply with the single word: OK")
    assert result.success, f"Failed: {result.error}"
    assert result.metadata.get("model") is not None


@pytest.mark.asyncio
async def test_health_check():
    from hub_core.agents.mammouth import MammouthAIAdapter

    adapter = MammouthAIAdapter("health-test", "claude-haiku-4-5")
    healthy = await adapter.health_check()
    assert healthy
