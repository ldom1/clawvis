"""Agent adapters and registry for multi-agent orchestration."""

from .base import AdapterStatus, AgentCapabilities, IAgentAdapter, TaskResult
from .mammouth import (
    MAMMOUTH_MODELS,
    ClaudeAdapter,
    DynamicMammouthAdapter,
    GeminiAdapter,
    MammouthAIAdapter,
    MistralAdapter,
)
from .openclaw import OpenClawAdapter
from .registry import AgentMetrics, AgentRegistry, HealthStatus, get_registry

__all__ = [
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
    "MAMMOUTH_MODELS",
]
