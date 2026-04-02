"""Pydantic models for hub_core API outputs. Missing data is represented as \"N/A\"."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

NA = Literal["N/A"]
NaOrFloat = float | NA
NaOrStr = str | NA
NaOrInt = int | NA


# --- Providers (providers.json) ---


class MammouthCredits(BaseModel):
    """MammouthAI credits from API or N/A."""

    available: NaOrFloat = Field(default="N/A")
    limit: NaOrFloat = Field(default="N/A")
    currency: str = "USD"


class MammouthUsage(BaseModel):
    """MammouthAI provider block."""

    provider: Literal["MammouthAI"] = "MammouthAI"
    credits: MammouthCredits = Field(default_factory=MammouthCredits)
    subscription: NaOrStr = Field(default="N/A")
    additional: NaOrStr = Field(default="N/A")
    last_updated: NaOrStr = Field(default="N/A")

    @classmethod
    def from_providers_mammouth_block(cls, m: dict) -> MammouthUsage:
        """Parse ``providers.json`` nested ``mammouth_ai`` object."""
        if not m:
            return cls()
        c = m.get("credits") or {}
        return cls(
            credits=MammouthCredits(
                available=c.get("available", "N/A"),
                limit=c.get("limit", "N/A"),
                currency=c.get("currency", "USD"),
            ),
            subscription=m.get("subscription", "N/A"),
            additional=m.get("additional", "N/A"),
            last_updated=m.get("last_updated", "N/A"),
        )

    def session_blob(self) -> dict:
        """Shape for ``session-tokens.json`` under key ``mammouth`` when API is configured."""
        return {
            "subscription": self.subscription,
            "credits": {
                "available": self.credits.available,
                "limit": self.credits.limit,
                "currency": self.credits.currency,
            },
            "last_updated": self.last_updated,
        }


class ProvidersResponse(BaseModel):
    """Root model for providers.json (MammouthAI only)."""

    mammouth_ai: MammouthUsage = Field(default_factory=MammouthUsage)
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


# --- System metrics (system.json) ---


class CpuRam(BaseModel):
    """CPU and RAM usage from /proc."""

    cpu_percent: float = Field(default=0.0, ge=0, le=100)
    ram_percent: float = Field(default=0.0, ge=0, le=100)
    ram_used_gb: float = Field(default=0.0, ge=0)
    ram_total_gb: float = Field(default=0.0, ge=0)
    # Disk usage for root filesystem
    disk_percent: float = Field(default=0.0, ge=0, le=100)
    disk_used_gb: float = Field(default=0.0, ge=0)
    disk_total_gb: float = Field(default=0.0, ge=0)


# --- Status (status.json) ---


class StatusResponse(BaseModel):
    """Usage status (Mammouth credits)."""

    mammouth_usage: MammouthUsage = Field(default_factory=MammouthUsage)
    last_check: str = Field(default_factory=lambda: datetime.now().isoformat())


# --- Hub state (main entry point aggregate) ---


class HubState(BaseModel):
    """All hub values in one structure; dumpable to dict. Token -1 becomes N/A."""

    providers: ProvidersResponse | None = None
    status: StatusResponse | None = None
    cpu_ram: CpuRam | None = None
    tokens_today: NaOrInt = Field(default="N/A")
    tokens_month: NaOrInt = Field(default="N/A")
    system_timestamp: NaOrStr = Field(default="N/A")
