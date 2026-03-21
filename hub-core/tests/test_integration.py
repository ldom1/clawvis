"""Integration test: agent identity, RBAC, network policy, adapters, and registry.

Usage:
  cd ~/Lab/clawvis/hub-core
  AGENT_ID=labos-orchestrator AGENT_ROLE=ORCHESTRATOR \\
  NETWORK_MODE=allowlist NETWORK_ALLOWLIST=api.anthropic.com,api.openai.com \\
  uv run pytest tests/test_integration.py -v
"""

import asyncio
import logging
import os
from typing import Dict

import pytest

# Force-set env vars for tests (override any value from .env)
os.environ["AGENT_ID"] = "labos-orchestrator"
os.environ["AGENT_ROLE"] = "ORCHESTRATOR"
os.environ["NETWORK_MODE"] = "allowlist"
os.environ["NETWORK_ALLOWLIST"] = "api.anthropic.com,api.openai.com"

from hub_core.security.identity import get_agent_identity, current_identity, reset_identity
from hub_core.security.rbac import require_capability, UnauthorizedError
from hub_core.security.network import get_network_policy
from hub_core.agents.registry import AgentRegistry, HealthStatus
from hub_core.agents.base import IAgentAdapter, TaskResult
from hub_core.agents.openclaw import OpenClawAdapter

logger = logging.getLogger(__name__)


@pytest.fixture(autouse=True)
def reset_identity_fixture():
    reset_identity()
    yield
    reset_identity()


def test_agent_identity_loads():
    identity = get_agent_identity()
    assert identity.agent_id == "labos-orchestrator"
    assert identity.has_capability("workflows.execute")


def test_network_policy_allows_essential():
    policy = get_network_policy()
    assert policy.is_allowed("api.anthropic.com")
    assert policy.is_allowed("localhost")
    assert not policy.is_allowed("evil.com")


def test_rbac_decorator_passes():
    @require_capability("workflows.execute")
    def protected():
        return "ok"

    assert protected() == "ok"


def test_rbac_decorator_denied():
    from hub_core.security.identity import AgentIdentity, AgentRole
    import hub_core.security.identity as ai

    viewer = AgentIdentity(
        agent_id="viewer",
        identity="viewer@labos.local",
        role=AgentRole.VIEWER,
        capabilities={"kanban.read"},
    )
    ai._current_identity = viewer

    @require_capability("workflows.execute")
    def protected():
        return "ok"

    with pytest.raises(UnauthorizedError):
        protected()


def test_agent_registry_register_and_select():
    registry = AgentRegistry()
    registry.register("openclaw-1", {"code.execute", "files.read"}, runtime="openclaw")
    registry.register("gemini-1", {"translation"}, runtime="gemini")

    best = registry.select_best_agent({"code.execute"})
    assert best == "openclaw-1"

    no_match = registry.select_best_agent({"unknown.capability"})
    assert no_match is None


@pytest.mark.asyncio
async def test_openclaw_adapter_executes():
    adapter = OpenClawAdapter("test-openclaw")
    result = await adapter.execute("echo hello")
    assert result.success
    assert result.cost_usd == 0.0


@pytest.mark.asyncio
async def test_openclaw_adapter_health():
    adapter = OpenClawAdapter()
    assert await adapter.health_check() is True
