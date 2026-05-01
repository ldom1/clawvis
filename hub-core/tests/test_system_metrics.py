#!/usr/bin/env python3
"""Tests for system metrics tracking (CPU, RAM)."""

from hub_core.update.system_metrics import get_cpu_ram


class TestSystemMetrics:
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

    def test_system_metrics_are_fresh(self):
        m1 = get_cpu_ram()
        m2 = get_cpu_ram()
        assert abs(m1.cpu_percent - m2.cpu_percent) < 20
        assert abs(m1.ram_percent - m2.ram_percent) < 20
