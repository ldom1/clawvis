"""Tests for hub_core.models."""

from hub_core.models import (
    CpuRam,
    HubState,
    MammouthCredits,
    MammouthUsage,
    ProvidersResponse,
    StatusResponse,
    token_or_na,
)


def test_mammouth_credits_na():
    m = MammouthCredits()
    assert m.available == "N/A"
    assert m.limit == "N/A"
    assert m.currency == "USD"


def test_mammouth_usage_real():
    m = MammouthUsage(
        credits=MammouthCredits(available=1.5, limit=2.0),
        subscription="$1.50 / $2.00",
        last_updated="12:00",
    )
    assert m.credits.available == 1.5
    assert m.credits.limit == 2.0


def test_providers_response_defaults():
    r = ProvidersResponse()
    assert r.mammouth_ai.credits.available == "N/A"
    assert r.timestamp and "T" in r.timestamp  # ISO format


def test_providers_response_roundtrip():
    r = ProvidersResponse(mammouth_ai=MammouthUsage())
    j = r.model_dump_json(indent=2)
    r2 = ProvidersResponse.model_validate_json(j)
    assert r2.mammouth_ai.credits.available == r.mammouth_ai.credits.available


def test_status_response_defaults():
    s = StatusResponse()
    assert s.last_check
    assert s.mammouth_usage is not None


def test_status_response_real():
    s = StatusResponse(
        mammouth_usage=MammouthUsage(credits=MammouthCredits(available=7.5, limit=12.0))
    )
    assert s.mammouth_usage.credits.available == 7.5
    d = s.model_dump()
    assert d["mammouth_usage"]["credits"]["available"] == 7.5


def test_token_or_na():
    assert token_or_na(100) == 100
    assert token_or_na(0) == 0
    assert token_or_na(-1) == "N/A"


def test_hub_state_dumpable():
    state = HubState(
        tokens_today=1000,
        tokens_month=30000,
        cpu_ram=CpuRam(cpu_percent=5.0, ram_percent=10.0),
    )
    d = state.model_dump()
    assert isinstance(d, dict)
    assert d["tokens_today"] == 1000
    assert d["tokens_month"] == 30000
    assert d["cpu_ram"]["cpu_percent"] == 5.0
    # CpuRam also exposes disk fields (may be 0.0 in tests)
    assert "disk_percent" in d["cpu_ram"]
    assert "disk_used_gb" in d["cpu_ram"]
    assert "disk_total_gb" in d["cpu_ram"]
    state_na = HubState(tokens_today="N/A", tokens_month="N/A")
    d2 = state_na.model_dump()
    assert d2["tokens_today"] == "N/A"
    assert d2["tokens_month"] == "N/A"
