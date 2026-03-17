"""LabOS Hub Core — metrics, providers, tokens, agents, and security."""

from .security import (
    AgentIdentity,
    AgentRole,
    get_agent_identity,
    current_identity,
    reset_identity,
    UnauthorizedError,
    require_capability,
    require_any_capability,
    fastapi_require_capability,
    RBACContext,
    NetworkPolicy,
    NetworkMode,
    get_network_policy,
)

from .agents import (
    IAgentAdapter,
    TaskResult,
    AgentCapabilities,
    AdapterStatus,
    AgentRegistry,
    AgentMetrics,
    HealthStatus,
    get_registry,
    OpenClawAdapter,
    MammouthAIAdapter,
    DynamicMammouthAdapter,
    ClaudeAdapter,
    GeminiAdapter,
    MistralAdapter,
)

__version__ = "1.0.0"
__all__ = [
    # Security / Identity
    "AgentIdentity", "AgentRole", "get_agent_identity", "current_identity", "reset_identity",
    # RBAC
    "UnauthorizedError", "require_capability", "require_any_capability",
    "fastapi_require_capability", "RBACContext",
    # Network
    "NetworkPolicy", "NetworkMode", "get_network_policy",
    # Agents
    "IAgentAdapter", "TaskResult", "AgentCapabilities", "AdapterStatus",
    "AgentRegistry", "AgentMetrics", "HealthStatus", "get_registry",
    "OpenClawAdapter", "MammouthAIAdapter", "DynamicMammouthAdapter",
    "ClaudeAdapter", "GeminiAdapter", "MistralAdapter",
]
