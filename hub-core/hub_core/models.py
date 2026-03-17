"""Pydantic models for hub_core API outputs. Missing data is represented as \"N/A\"."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

NA = Literal["N/A"]
NaOrFloat = float | NA
NaOrStr = str | NA
NaOrInt = int | NA


def token_or_na(value: int) -> int | NA:
    """Return value or \"N/A\" if token sentinel -1."""
    return value if value != -1 else "N/A"


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
