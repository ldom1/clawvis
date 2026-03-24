"""Agent registry and health monitoring for multi-agent orchestration."""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class AgentMetrics:
    agent_id: str
    capabilities: set = field(default_factory=set)
    uptime_percent: float = 100.0
    response_time_ms: float = 0.0
    last_health_check: datetime = field(default_factory=datetime.now)
    consecutive_failures: int = 0
    total_tasks: int = 0
    successful_tasks: int = 0
    failed_tasks: int = 0
    cost_usd: float = 0.0
    tokens_used: int = 0
    version: str = "1.0"
    runtime: str = "unknown"

    @property
    def success_rate(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return (self.successful_tasks / self.total_tasks) * 100.0

    @property
    def cost_per_task(self) -> float:
        if self.total_tasks == 0:
            return 0.0
        return self.cost_usd / self.total_tasks

    @property
    def health_status(self) -> HealthStatus:
        if self.consecutive_failures > 5:
            return HealthStatus.UNHEALTHY
        if self.uptime_percent < 95 or self.response_time_ms > 5000:
            return HealthStatus.DEGRADED
        if (
            self.uptime_percent >= 95
            and self.response_time_ms <= 5000
            and self.consecutive_failures < 2
        ):
            return HealthStatus.HEALTHY
        return HealthStatus.UNKNOWN

    def record_success(
        self, response_time_ms: float, cost_usd: float = 0.0, tokens: int = 0
    ):
        self.total_tasks += 1
        self.successful_tasks += 1
        self.consecutive_failures = 0
        self.response_time_ms = (
            self.response_time_ms * (self.total_tasks - 1) + response_time_ms
        ) / self.total_tasks
        self.cost_usd += cost_usd
        self.tokens_used += tokens
        self.last_health_check = datetime.now()

    def record_failure(self, response_time_ms: float = 0.0):
        self.total_tasks += 1
        self.failed_tasks += 1
        self.consecutive_failures += 1
        if self.total_tasks > 0:
            self.uptime_percent = (self.successful_tasks / self.total_tasks) * 100
        self.last_health_check = datetime.now()

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "health_status": self.health_status.value,
            "uptime_percent": round(self.uptime_percent, 2),
            "response_time_ms": round(self.response_time_ms, 2),
            "success_rate": round(self.success_rate, 2),
            "total_tasks": self.total_tasks,
            "cost_usd": round(self.cost_usd, 4),
            "cost_per_task": round(self.cost_per_task, 4),
            "consecutive_failures": self.consecutive_failures,
            "runtime": self.runtime,
            "version": self.version,
            "last_check": self.last_health_check.isoformat(),
        }


class AgentRegistry:
    """Central registry tracking agent health, cost, and selection."""

    def __init__(self):
        self.agents: Dict[str, AgentMetrics] = {}
        self._health_check_task: Optional[asyncio.Task] = None

    def register(
        self, agent_id: str, capabilities: set, runtime: str = "unknown"
    ) -> AgentMetrics:
        metrics = AgentMetrics(
            agent_id=agent_id, capabilities=capabilities, runtime=runtime
        )
        self.agents[agent_id] = metrics
        logger.info(f"Registered agent: {agent_id} ({runtime})")
        return metrics

    def unregister(self, agent_id: str) -> bool:
        if agent_id in self.agents:
            del self.agents[agent_id]
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        return False

    def get_agent(self, agent_id: str) -> Optional[AgentMetrics]:
        return self.agents.get(agent_id)

    def get_all_agents(self) -> Dict[str, AgentMetrics]:
        return self.agents.copy()

    def get_healthy_agents(self) -> List[AgentMetrics]:
        return sorted(
            [
                m
                for m in self.agents.values()
                if m.health_status == HealthStatus.HEALTHY
            ],
            key=lambda m: m.success_rate,
            reverse=True,
        )

    def select_best_agent(
        self, required_capabilities: set, optimize_for: str = "quality"
    ) -> Optional[str]:
        candidates = [
            m
            for m in self.agents.values()
            if required_capabilities.issubset(m.capabilities)
            and m.health_status != HealthStatus.UNHEALTHY
        ]
        if not candidates:
            logger.warning(f"No agents available for: {required_capabilities}")
            return None

        if optimize_for == "cost":
            best = min(candidates, key=lambda m: (m.cost_per_task, -m.success_rate))
        elif optimize_for == "speed":
            best = min(candidates, key=lambda m: (m.response_time_ms, -m.success_rate))
        else:  # quality
            best = max(candidates, key=lambda m: (m.success_rate, -m.cost_per_task))

        logger.info(f"Selected {best.agent_id} (optimize={optimize_for})")
        return best.agent_id

    def get_registry_status(self) -> dict:
        agents = list(self.agents.values())
        if not agents:
            return {
                "total_agents": 0,
                "healthy_agents": 0,
                "avg_success_rate": 0,
                "total_cost_usd": 0,
            }

        healthy = sum(1 for m in agents if m.health_status == HealthStatus.HEALTHY)
        avg_success = sum(m.success_rate for m in agents) / len(agents)

        return {
            "total_agents": len(agents),
            "healthy_agents": healthy,
            "degraded_agents": sum(
                1 for m in agents if m.health_status == HealthStatus.DEGRADED
            ),
            "unhealthy_agents": sum(
                1 for m in agents if m.health_status == HealthStatus.UNHEALTHY
            ),
            "avg_success_rate": round(avg_success, 2),
            "total_tasks": sum(m.total_tasks for m in agents),
            "total_cost_usd": round(sum(m.cost_usd for m in agents), 4),
            "agents": [m.to_dict() for m in agents],
        }

    async def start_health_check(self, interval_seconds: int = 60):
        if self._health_check_task and not self._health_check_task.done():
            return
        self._health_check_task = asyncio.create_task(
            self._health_check_loop(interval_seconds)
        )

    async def stop_health_check(self):
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

    async def _health_check_loop(self, interval_seconds: int):
        while True:
            try:
                healthy = sum(
                    1
                    for m in self.agents.values()
                    if m.health_status == HealthStatus.HEALTHY
                )
                logger.debug(f"Health: {healthy}/{len(self.agents)} agents healthy")
                await asyncio.sleep(interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
                await asyncio.sleep(interval_seconds)


_registry: Optional[AgentRegistry] = None


def get_registry() -> AgentRegistry:
    global _registry
    if _registry is None:
        _registry = AgentRegistry()
    return _registry
