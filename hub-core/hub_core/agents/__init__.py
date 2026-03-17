"""Agent adapters and registry for multi-agent orchestration."""

from .base import IAgentAdapter, TaskResult, AgentCapabilities, AdapterStatus
from .registry import AgentRegistry, AgentMetrics, HealthStatus, get_registry
from .openclaw import OpenClawAdapter
from .mammouth import (
    MammouthAIAdapter,
    DynamicMammouthAdapter,
    ClaudeAdapter,
    GeminiAdapter,
    MistralAdapter,
    MAMMOUTH_MODELS,
)

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
