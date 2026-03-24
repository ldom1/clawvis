#!/usr/bin/env python3
"""Tests for system metrics tracking (CPU, RAM, tokens, water)."""

from unittest.mock import patch

from hub_core.track.system import get_system_stats
from hub_core.track.tokens import get_token_stats


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

    def test_get_system_stats_returns_dict(self):
        metrics = get_system_stats()
        assert isinstance(metrics, dict)
        assert "cpu_percent" in metrics
        assert "ram_percent" in metrics

    def test_cpu_ram_values_in_range(self):
        metrics = get_system_stats()
        assert 0 <= metrics["cpu_percent"] <= 100
        assert 0 <= metrics["ram_percent"] <= 100

    def test_cpu_ram_are_floats(self):
        metrics = get_system_stats()
        assert isinstance(metrics["cpu_percent"], (int, float))
        assert isinstance(metrics["ram_percent"], (int, float))


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
        metrics = get_system_stats()
        tokens = get_token_stats()
        assert metrics["cpu_percent"] is not None
        assert metrics["ram_percent"] is not None
        assert tokens is not None

    def test_system_metrics_are_fresh(self):
        metrics1 = get_system_stats()
        metrics2 = get_system_stats()
        assert abs(metrics1["cpu_percent"] - metrics2["cpu_percent"]) < 20
        assert abs(metrics1["ram_percent"] - metrics2["ram_percent"]) < 20
