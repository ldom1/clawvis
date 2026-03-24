"""Agent identity and capability management for Clawvis.

Each agent has an explicit identity (e.g., labos-orchestrator@labos.local),
a role, and a capability set. Actions are auditable. No delegation.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Set


class AgentRole(Enum):
    ORCHESTRATOR = "orchestrator"
    AGENT = "agent"
    VIEWER = "viewer"

    def __lt__(self, other):
        hierarchy = {AgentRole.ORCHESTRATOR: 3, AgentRole.AGENT: 2, AgentRole.VIEWER: 1}
        return hierarchy[self] < hierarchy[other]


@dataclass
class AgentIdentity:
    agent_id: str
    identity: str
    role: AgentRole
    capabilities: Set[str]
    network_allowlist: Optional[list] = None
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if not self.identity:
            self.identity = f"{self.agent_id}@labos.local"

    def has_capability(self, required: str) -> bool:
        if self.role == AgentRole.ORCHESTRATOR and "*" in self.capabilities:
            return True
        return required in self.capabilities

    def to_audit_log(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "identity": self.identity,
            "role": self.role.value,
            "capabilities": sorted(self.capabilities),
            "timestamp": self.created_at.isoformat(),
        }

    def __repr__(self) -> str:
        return f"AgentIdentity(id={self.agent_id}, role={self.role.value})"


def get_capabilities(role: AgentRole) -> Set[str]:
    """Return the capability set for a given role (least privilege)."""
    sets = {
        AgentRole.ORCHESTRATOR: {
            "*",
            "kanban.read",
            "kanban.write",
            "kanban.delete",
            "logs.read",
            "logs.write",
            "agents.list",
            "agents.health",
            "agents.manage",
            "workflows.list",
            "workflows.execute",
            "workflows.manage",
            "network.configure",
        },
        AgentRole.AGENT: {
            "kanban.read",
            "kanban.write",
            "logs.read",
            "logs.write",
            "agents.list",
            "agents.health",
            "workflows.list",
            "workflows.execute",
        },
        AgentRole.VIEWER: {
            "kanban.read",
            "logs.read",
            "agents.list",
            "agents.health",
            "workflows.list",
        },
    }
    return sets.get(role, set())


def get_agent_identity() -> AgentIdentity:
    """Load agent identity from environment variables.

    Required: AGENT_ID
    Optional: AGENT_IDENTITY, AGENT_ROLE, NETWORK_ALLOWLIST
    """
    agent_id = os.getenv("AGENT_ID") or os.getenv("AGENT_NAME")
    if not agent_id:
        raise ValueError("AGENT_ID environment variable required")

    identity = os.getenv("AGENT_IDENTITY", f"{agent_id}@labos.local")

    role_str = os.getenv("AGENT_ROLE", "AGENT").upper()
    try:
        role = AgentRole[role_str]
    except KeyError:
        raise ValueError(
            f"Invalid AGENT_ROLE: {role_str}. Must be one of: {[r.name for r in AgentRole]}"
        )

    network_allowlist = None
    if allowlist_str := os.getenv("NETWORK_ALLOWLIST"):
        network_allowlist = [d.strip() for d in allowlist_str.split(",") if d.strip()]

    return AgentIdentity(
        agent_id=agent_id,
        identity=identity,
        role=role,
        capabilities=get_capabilities(role),
        network_allowlist=network_allowlist,
    )


_current_identity: Optional[AgentIdentity] = None


def current_identity() -> AgentIdentity:
    global _current_identity
    if _current_identity is None:
        _current_identity = get_agent_identity()
    return _current_identity


def reset_identity():
    """Reset cached identity (testing only)."""
    global _current_identity
    _current_identity = None
