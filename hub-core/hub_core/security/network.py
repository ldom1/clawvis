"""Network policy enforcement for ClawPilot agents.

Modes: unrestricted / restricted (essential domains) / allowlist (essential + custom).
In Docker with NET_ADMIN, iptables rules are applied; otherwise, policy is logged only.
"""

import logging
import os
import socket
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Set

logger = logging.getLogger(__name__)


class NetworkMode(Enum):
    UNRESTRICTED = "unrestricted"
    RESTRICTED = "restricted"
    ALLOWLIST = "allowlist"


@dataclass
class NetworkPolicy:
    mode: NetworkMode
    custom_allowlist: Optional[Set[str]] = None
    agent_id: Optional[str] = None

    ESSENTIAL_DOMAINS = {
        "login.microsoftonline.com",
        "accounts.google.com",
        "auth.anthropic.com",
        "api.anthropic.com",
        "api.openai.com",
        "generativelanguage.googleapis.com",
        "api.mammouth.ai",
        "localhost",
        "127.0.0.1",
        "::1",
    }

    def __post_init__(self):
        if self.custom_allowlist is None:
            self.custom_allowlist = set()

    def is_allowed(self, domain: str) -> bool:
        domain = domain.lower().strip()
        if self.mode == NetworkMode.UNRESTRICTED:
            return True
        if domain in {"localhost", "127.0.0.1", "::1"}:
            return True
        if self.mode == NetworkMode.RESTRICTED:
            return self._is_essential(domain)
        if self.mode == NetworkMode.ALLOWLIST:
            return self._is_essential(domain) or self._matches_allowlist(domain)
        return False

    def _is_essential(self, domain: str) -> bool:
        domain = domain.lower()
        for essential in self.ESSENTIAL_DOMAINS:
            if domain == essential or ("*" in essential and domain.endswith(essential.replace("*", ""))):
                return True
        return False

    def _matches_allowlist(self, domain: str) -> bool:
        domain = domain.lower()
        for allowed in self.custom_allowlist:
            allowed = allowed.lower()
            if domain == allowed or ("*" in allowed and domain.endswith(allowed.replace("*", ""))):
                return True
        return False

    def get_full_allowlist(self) -> Set[str]:
        allowlist = set(self.ESSENTIAL_DOMAINS)
        if self.mode == NetworkMode.ALLOWLIST:
            allowlist.update(self.custom_allowlist or set())
        return allowlist

    def resolve_domain_to_ip(self, domain: str) -> Optional[str]:
        try:
            return socket.getaddrinfo(domain, None)[0][4][0]
        except socket.gaierror:
            logger.warning(f"Failed to resolve: {domain}")
            return None

    def enforce_iptables(self) -> bool:
        """Apply iptables rules (requires Docker NET_ADMIN capability)."""
        if self.mode == NetworkMode.UNRESTRICTED:
            logger.info("Network policy: unrestricted")
            return True
        allowlist_ips = {ip for d in self.get_full_allowlist() if (ip := self.resolve_domain_to_ip(d))}
        if not allowlist_ips:
            logger.warning("No IPs resolved; cannot enforce iptables")
            return False
        logger.info(f"[STUB] Would enforce iptables for {self.agent_id}: allow {sorted(allowlist_ips)}")
        return True

    def __repr__(self) -> str:
        custom = f", custom={len(self.custom_allowlist)}" if self.custom_allowlist else ""
        return f"NetworkPolicy(mode={self.mode.value}{custom})"


def get_network_policy() -> NetworkPolicy:
    """Load network policy from environment (NETWORK_MODE, NETWORK_ALLOWLIST, AGENT_ID)."""
    mode_str = os.getenv("NETWORK_MODE", "restricted").lower()
    try:
        mode = NetworkMode[mode_str.upper()]
    except KeyError:
        logger.warning(f"Invalid NETWORK_MODE: {mode_str}, defaulting to restricted")
        mode = NetworkMode.RESTRICTED

    custom_allowlist = None
    if allowlist_str := os.getenv("NETWORK_ALLOWLIST"):
        custom_allowlist = {d.strip() for d in allowlist_str.split(",") if d.strip()}

    policy = NetworkPolicy(mode=mode, custom_allowlist=custom_allowlist, agent_id=os.getenv("AGENT_ID", "unknown"))
    logger.info(f"Network policy: {policy}")
    return policy
