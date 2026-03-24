"""Tests for hub_core.main: get_hub_state and main."""

from unittest.mock import patch

import pytest

from hub_core.main import get_hub_state, main
from hub_core.models import (
    CpuRam,
    HubState,
    MammouthUsage,
    ProvidersResponse,
    StatusResponse,
)

# New session-based token stats format returned by get_token_stats()
_MOCK_TOKEN_STATS = {
    "claude": {
        "usage_percent": 22.5,
        "tokens_used": "65.8k",
        "tokens_limit": "300k",
        "reset_time": "19:00 UTC",
    },
    "mammouth": {
        "subscription": "pro",
        "credits": {"available": 100.0, "limit": 200.0, "currency": "EUR"},
    },
    "timestamp": "2026-02-26T12:00:00",
}


@pytest.fixture
def mock_providers():
    return ProvidersResponse(mammouth_ai=MammouthUsage())


@pytest.fixture
def mock_status():
    return StatusResponse()


@pytest.fixture
def mock_cpu_ram():
    return CpuRam(
        cpu_percent=10.5, ram_percent=42.0, ram_used_gb=6.0, ram_total_gb=15.0
    )


@pytest.fixture
def mock_token_stats():
    return _MOCK_TOKEN_STATS


@patch("hub_core.main.get_hub_state")
def test_main_returns_hub_state(mock_get_hub_state):
    mock_get_hub_state.return_value = HubState()
    out = main()
    assert isinstance(out, HubState)
    mock_get_hub_state.assert_called_once_with(write_json=True)


@patch("hub_core.track.tokens.get_token_stats")
@patch("hub_core.update.system_metrics.get_cpu_ram")
@patch("hub_core.update.status.get_status_response")
@patch("hub_core.fetch.provider_data.get_providers_response")
def test_get_hub_state_full(
    mock_get_providers,
    mock_get_status,
    mock_get_cpu_ram,
    mock_get_token_stats,
    mock_providers,
    mock_status,
    mock_cpu_ram,
    mock_token_stats,
):
    mock_get_providers.return_value = mock_providers
    mock_get_status.return_value = mock_status
    mock_get_cpu_ram.return_value = mock_cpu_ram
    mock_get_token_stats.return_value = mock_token_stats

    state = get_hub_state(write_json=False)

    assert isinstance(state, HubState)
    assert state.providers is mock_providers
    assert state.providers.mammouth_ai is not None
    assert state.status is mock_status
    assert state.status.mammouth_usage is not None
    assert state.cpu_ram is mock_cpu_ram
    assert state.cpu_ram.cpu_percent == 10.5
    assert state.cpu_ram.ram_percent == 42.0
    # tokens are always "N/A" (openclaw status gives % not absolute counts)
    assert state.tokens_today == "N/A"
    assert state.tokens_month == "N/A"
    assert state.system_timestamp

    d = state.model_dump()
    assert set(d.keys()) == {
        "providers",
        "status",
        "cpu_ram",
        "tokens_today",
        "tokens_month",
        "system_timestamp",
    }
    assert d["tokens_today"] == "N/A"
    assert d["tokens_month"] == "N/A"
    assert d["cpu_ram"]["cpu_percent"] == 10.5
    assert "mammouth_ai" in d["providers"]
    assert "mammouth_usage" in d["status"]


@patch("hub_core.track.tokens.get_token_stats")
@patch("hub_core.update.system_metrics.get_cpu_ram")
@patch("hub_core.update.status.get_status_response")
@patch("hub_core.fetch.provider_data.get_providers_response")
def test_get_hub_state_structure_and_dump(
    mock_get_providers,
    mock_get_status,
    mock_get_cpu_ram,
    mock_get_token_stats,
):
    mock_get_providers.return_value = ProvidersResponse(mammouth_ai=MammouthUsage())
    mock_get_status.return_value = StatusResponse()
    mock_get_cpu_ram.return_value = CpuRam(
        cpu_percent=0, ram_percent=0, ram_used_gb=0, ram_total_gb=0
    )
    mock_get_token_stats.return_value = _MOCK_TOKEN_STATS

    state = get_hub_state(write_json=False)

    assert state.providers is not None
    assert state.status is not None
    assert state.cpu_ram is not None
    assert state.tokens_today == "N/A"
    assert state.tokens_month == "N/A"
    assert state.system_timestamp != "N/A"

    d = state.model_dump()
    assert isinstance(d, dict)
    assert "providers" in d and "status" in d and "cpu_ram" in d
    assert d["tokens_today"] == "N/A"
    assert d["tokens_month"] == "N/A"
    assert "system_timestamp" in d

    j = state.model_dump_json()
    assert "providers" in j and "cpu_ram" in j


@patch("hub_core.track.tokens.get_token_stats")
@patch("hub_core.update.system_metrics.get_cpu_ram")
@patch("hub_core.update.status.get_status_response")
@patch("hub_core.fetch.provider_data.get_providers_response")
def test_get_hub_state_token_or_na(
    mock_get_providers,
    mock_get_status,
    mock_get_cpu_ram,
    mock_get_token_stats,
):
    """tokens_today and tokens_month are always N/A (openclaw status gives % not counts)."""
    mock_get_providers.return_value = ProvidersResponse()
    mock_get_status.return_value = StatusResponse()
    mock_get_cpu_ram.return_value = CpuRam()
    mock_get_token_stats.return_value = _MOCK_TOKEN_STATS

    state = get_hub_state(write_json=False)

    assert state.tokens_today == "N/A"
    assert state.tokens_month == "N/A"


@patch("hub_core.track.tokens.get_token_stats")
@patch("hub_core.update.system_metrics.get_cpu_ram")
@patch("hub_core.update.status.get_status_response")
@patch("hub_core.fetch.provider_data.get_providers_response")
def test_get_simple_state_shape(
    mock_get_providers,
    mock_get_status,
    mock_get_cpu_ram,
    mock_get_token_stats,
    mock_providers,
    mock_status,
    mock_cpu_ram,
    mock_token_stats,
):
    from hub_core.main import get_simple_state

    mock_get_providers.return_value = mock_providers
    mock_get_status.return_value = mock_status
    mock_get_cpu_ram.return_value = mock_cpu_ram
    mock_get_token_stats.return_value = mock_token_stats

    d = get_simple_state(write_json=False)

    assert set(d.keys()) == {"providers", "system_info", "system_timestamp"}
    llm = d["providers"]["llm_providers"]
    assert "mammouth_ai" in llm
    assert (
        llm["mammouth_ai"]["credits_available"]
        == mock_providers.mammouth_ai.credits.available
    )
    assert "cpu_percent" in d["system_info"]
    assert "ram_percent" in d["system_info"]
