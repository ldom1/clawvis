#!/usr/bin/env python3
"""Tests for system metrics tracking (CPU, RAM, tokens, water)."""

from unittest.mock import patch

from hub_core.track.tokens import get_token_stats
from hub_core.update.system_metrics import get_cpu_ram

MOCK_SESSION_DATA = {
    "updated_at": "2026-03-17T10:00:00",
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
}


class TestSystemMetrics:
    """Tests for CPU and RAM tracking."""

    def test_get_cpu_ram_returns_model(self):
        m = get_cpu_ram()
        assert m.cpu_percent is not None
        assert m.ram_percent is not None

    def test_cpu_ram_values_in_range(self):
        m = get_cpu_ram()
        assert 0 <= m.cpu_percent <= 100
        assert 0 <= m.ram_percent <= 100

    def test_cpu_ram_are_numeric(self):
        m = get_cpu_ram()
        assert isinstance(m.cpu_percent, (int, float))
        assert isinstance(m.ram_percent, (int, float))


class TestTokenTracking:
    """Tests for token usage tracking."""

    @patch(
        "hub_core.track.tokens.update_session_tokens", return_value=MOCK_SESSION_DATA
    )
    def test_get_token_stats_returns_dict(self, _mock):
        stats = get_token_stats()
        assert isinstance(stats, dict)

    @patch(
        "hub_core.track.tokens.update_session_tokens", return_value=MOCK_SESSION_DATA
    )
    def test_token_stats_has_keys(self, _mock):
        stats = get_token_stats()
        assert "claude" in stats
        assert "mammouth" in stats
        assert "timestamp" in stats

    @patch(
        "hub_core.track.tokens.update_session_tokens", return_value=MOCK_SESSION_DATA
    )
    def test_token_values_valid(self, _mock):
        stats = get_token_stats()
        assert isinstance(stats["claude"], dict)
        assert isinstance(stats["mammouth"], dict)


class TestIntegration:
    """Integration tests for all system metrics."""

    @patch(
        "hub_core.track.tokens.update_session_tokens", return_value=MOCK_SESSION_DATA
    )
    def test_complete_system_metrics_fetch(self, _mock):
        m = get_cpu_ram()
        tokens = get_token_stats()
        assert m.cpu_percent is not None
        assert m.ram_percent is not None
        assert tokens is not None

    def test_system_metrics_are_fresh(self):
        m1 = get_cpu_ram()
        m2 = get_cpu_ram()
        assert abs(m1.cpu_percent - m2.cpu_percent) < 20
        assert abs(m1.ram_percent - m2.ram_percent) < 20
