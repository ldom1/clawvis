#!/usr/bin/env python3
"""Tests for service lifecycle management."""

from unittest.mock import MagicMock, patch

from hub_core.services import (
    ServiceManager,
    get_service_status,
    start_service,
    stop_service,
)
from hub_core.services.manager import SERVICES


class TestServiceManager:
    """Tests for ServiceManager."""

    def test_services_defined(self):
        """Test that services are defined."""
        assert len(SERVICES) > 0
        expected_services = ["debate", "messidor", "optimizer"]
        for svc in expected_services:
            assert svc in SERVICES

    def test_service_object_structure(self):
        """Test that service objects have required attributes."""
        for service_id, service in SERVICES.items():
            assert hasattr(service, "name")
            assert hasattr(service, "port")
            assert hasattr(service, "process_name")
            assert hasattr(service, "start_cmd")

    def test_get_all_services(self):
        """Test getting status of all services."""
        all_services = ServiceManager.get_all_services()
        assert isinstance(all_services, dict)
        assert len(all_services) > 0

        # Each should have status info
        for service_id, status in all_services.items():
            assert "running" in status
            assert "name" in status
            assert "port" in status

    def test_get_status_unknown_service(self):
        """Test getting status of unknown service."""
        result = ServiceManager.get_status("unknown-service")
        assert "error" in result
        assert "Unknown service" in result["error"]

    def test_get_status_valid_service(self):
        """Test getting status of valid service."""
        result = ServiceManager.get_status("debate")
        assert "error" not in result
        assert "running" in result
        assert "name" in result
        assert "port" in result
        assert "ram_mb" in result

    @patch("hub_core.services.manager.subprocess.Popen")
    def test_start_service(self, mock_popen):
        """Test starting a service."""
        mock_popen.return_value = MagicMock()

        result = start_service("debate")
        assert "success" in result
        assert "message" in result

    @patch("hub_core.services.manager.subprocess.run")
    def test_stop_service(self, mock_run):
        """Test stopping a service."""
        mock_run.return_value = MagicMock(returncode=0)

        result = stop_service("debate")
        assert isinstance(result, dict)
        # Result varies depending on if service was running
        assert "success" in result or "message" in result


class TestServiceStatus:
    """Tests for service status detection."""

    def test_debate_service_exists(self):
        """Test that Debate Arena service is defined."""
        assert "debate" in SERVICES
        svc = SERVICES["debate"]
        assert svc.port == 3010
        assert "next" in svc.process_name.lower()

    def test_messidor_service_exists(self):
        """Test that Messidor service is defined."""
        assert "messidor" in SERVICES
        svc = SERVICES["messidor"]
        assert svc.port == 8501
        assert "streamlit" in svc.process_name.lower()

    def test_optimizer_service_exists(self):
        """Test that Optimizer service is defined."""
        assert "optimizer" in SERVICES
        svc = SERVICES["optimizer"]
        assert svc.port == 8000
        assert "uvicorn" in svc.process_name.lower()


class TestRAMEstimation:
    """Tests for RAM usage estimation."""

    def test_all_services_have_ram_estimate(self):
        """Test that all services have RAM estimates."""
        for service_id, service in SERVICES.items():
            assert service.ram_mb is not None
            assert service.ram_mb > 0

    def test_ram_reasonable_values(self):
        """Test that RAM estimates are reasonable."""
        for service_id, service in SERVICES.items():
            # Typical Node/Python service: 100-500MB
            assert 50 < service.ram_mb < 500, (
                f"{service.name} RAM estimate unreasonable"
            )

    def test_messidor_higher_ram(self):
        """Test that Streamlit gets higher RAM estimate (ML model loaded)."""
        messidor_ram = SERVICES["messidor"].ram_mb
        debate_ram = SERVICES["debate"].ram_mb
        assert messidor_ram >= debate_ram  # Messidor typically uses more


class TestServiceCommands:
    """Tests for convenience functions."""

    def test_get_service_status_function(self):
        """Test get_service_status convenience function."""
        result = get_service_status("debate")
        assert isinstance(result, dict)
        assert "running" in result

    def test_start_service_function(self):
        """Test start_service convenience function."""
        with patch("hub_core.services.manager.ServiceManager.start") as mock:
            mock.return_value = {"success": True}
            result = start_service("debate")
            assert result["success"]

    def test_stop_service_function(self):
        """Test stop_service convenience function."""
        with patch("hub_core.services.manager.ServiceManager.stop") as mock:
            mock.return_value = {"success": True}
            result = stop_service("debate")
            assert result["success"]
