"""Abstract interface and data types for agent adapters."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class AdapterStatus(Enum):
    OK = "ok"
    DEGRADED = "degraded"
    ERROR = "error"


@dataclass
class TaskResult:
    success: bool
    output: str
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    cost_usd: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentCapabilities:
    agent_id: str
    runtime: str
    version: str
    can_read_files: bool = True
    can_write_files: bool = True
    can_execute_code: bool = True
    max_context_tokens: int = 128000
    supports_streaming: bool = False
    estimated_cost_per_1k_tokens: float = 0.0


class IAgentAdapter(ABC):
    """Uniform interface for all agent adapters.

    Adapters are dumb translators — intelligence lives in the router and orchestrator.
    """

    @abstractmethod
    async def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> TaskResult:
        """Execute a task via this agent."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the agent is healthy."""

    @abstractmethod
    def get_capabilities(self) -> AgentCapabilities:
        """Return capabilities descriptor."""

    @abstractmethod
    def get_status(self) -> AdapterStatus:
        """Return current adapter status."""
