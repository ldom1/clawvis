"""Clawvis Hub Core — metrics, providers, tokens, agents, and security."""

from .agents import (
    AdapterStatus,
    AgentCapabilities,
    AgentMetrics,
    AgentRegistry,
    ClaudeAdapter,
    DynamicMammouthAdapter,
    GeminiAdapter,
    HealthStatus,
    IAgentAdapter,
    MammouthAIAdapter,
    MistralAdapter,
    OpenClawAdapter,
    TaskResult,
    get_registry,
)
from .security import (
    AgentIdentity,
    AgentRole,
    NetworkMode,
    NetworkPolicy,
    RBACContext,
    UnauthorizedError,
    current_identity,
    fastapi_require_capability,
    get_agent_identity,
    get_network_policy,
    require_any_capability,
    require_capability,
    reset_identity,
)
from .brain_memory import active_brain_memory_root

__version__ = "1.0.0"
__all__ = [
    "active_brain_memory_root",
    # Security / Identity
    "AgentIdentity",
    "AgentRole",
    "get_agent_identity",
    "current_identity",
    "reset_identity",
    # RBAC
    "UnauthorizedError",
    "require_capability",
    "require_any_capability",
    "fastapi_require_capability",
    "RBACContext",
    # Network
    "NetworkPolicy",
    "NetworkMode",
    "get_network_policy",
    # Agents
    "IAgentAdapter",
    "TaskResult",
    "AgentCapabilities",
    "AdapterStatus",
    "AgentRegistry",
    "AgentMetrics",
    "HealthStatus",
    "get_registry",
    "OpenClawAdapter",
    "MammouthAIAdapter",
    "DynamicMammouthAdapter",
    "ClaudeAdapter",
    "GeminiAdapter",
    "MistralAdapter",
]
