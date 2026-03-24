#!/usr/bin/env python3
"""Service lifecycle management - start/stop Lab services."""

import subprocess
import psutil
from typing import Dict, Optional
from dataclasses import dataclass

from loguru import logger
from hub_core.config import LAB_DIR


@dataclass
class Service:
    """Service definition."""

    name: str
    port: int
    process_name: str  # Part of command to identify process
    start_cmd: str  # Command to start service
    stop_method: str = "pkill"  # "pkill" or "pm2"
    ram_mb: Optional[float] = None  # Estimated RAM usage in MB


# Define all Lab services
SERVICES = {
    "debate": Service(
        name="Debate Arena",
        port=3010,
        process_name="next dev --port 3010",
        start_cmd=f"cd {LAB_DIR / 'project' / 'debate-arena'} && npm run dev -- --port 3010",
        ram_mb=180,
    ),
    "messidor": Service(
        name="Messidor",
        port=8501,
        process_name="streamlit run",
        start_cmd=f"cd {LAB_DIR / 'project' / 'messidor'} && uv run streamlit run app/streamlit_app.py --server.port 8501",
        ram_mb=250,
    ),
    "optimizer": Service(
        name="Optimizer API",
        port=8000,
        process_name="uvicorn.*8000",
        start_cmd=f"cd {LAB_DIR / 'project' / 'optimizer-arena' / 'backend'} && uv run uvicorn src.main:app --port 8000",
        ram_mb=150,
    ),
    "melodimage": Service(
        name="Melodimage (statique)",
        port=8088,
        process_name="melodimage-static-placeholder",
        start_cmd="echo 'Melodimage est une app statique servie par Nginx (rien à démarrer côté hub_core).'",
        ram_mb=80,
    ),
    "poetic_shield": Service(
        name="Poetic Shield (statique)",
        port=8088,
        process_name="poetic-shield-static-placeholder",
        start_cmd="echo 'Poetic Shield est une app statique servie par Nginx (rien à démarrer côté hub_core).'",
        ram_mb=80,
    ),
}


class ServiceManager:
    """Manage Lab service lifecycle."""

    @staticmethod
    def get_all_services() -> Dict[str, Dict]:
        """Get status of all services."""
        result = {}
        for service_id, service in SERVICES.items():
            result[service_id] = ServiceManager.get_status(service_id)
        return result

    @staticmethod
    def get_status(service_id: str) -> Dict:
        """Get status of a single service."""
        if service_id not in SERVICES:
            return {"error": f"Unknown service: {service_id}"}

        service = SERVICES[service_id]

        # Check if running
        running = False
        pid = None
        ram_used = 0

        for proc in psutil.process_iter(["pid", "name", "cmdline"]):
            try:
                cmdline = " ".join(proc.info["cmdline"] or [])
                if service.process_name in cmdline:
                    running = True
                    pid = proc.info["pid"]
                    try:
                        ram_used = proc.memory_info().rss / 1024 / 1024  # MB
                    except Exception:
                        ram_used = service.ram_mb or 0
                    break
            except Exception:
                continue

        return {
            "id": service_id,
            "name": service.name,
            "running": running,
            "port": service.port,
            "pid": pid,
            "ram_mb": round(ram_used, 1),
            "estimated_ram_mb": service.ram_mb,
        }

    @staticmethod
    def start(service_id: str) -> Dict:
        """Start a service."""
        if service_id not in SERVICES:
            return {"error": f"Unknown service: {service_id}", "success": False}

        status = ServiceManager.get_status(service_id)
        if status["running"]:
            return {"message": f"{status['name']} already running", "success": True}

        service = SERVICES[service_id]
        logger.info("Starting {}: {}", service.name, service.start_cmd)

        try:
            subprocess.Popen(
                service.start_cmd,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            logger.info("{} started successfully", service.name)
            return {
                "success": True,
                "message": f"{service.name} started",
                "service_id": service_id,
            }
        except Exception as e:
            logger.error("Failed to start {}: {}", service.name, e)
            return {
                "success": False,
                "error": str(e),
            }

    @staticmethod
    def stop(service_id: str) -> Dict:
        """Stop a service to free RAM."""
        if service_id not in SERVICES:
            return {"error": f"Unknown service: {service_id}", "success": False}

        status = ServiceManager.get_status(service_id)
        if not status["running"]:
            return {"message": f"{status['name']} not running", "success": True}

        service = SERVICES[service_id]
        logger.info("Stopping {}", service.name)

        try:
            # Kill by process name
            subprocess.run(
                f"pkill -f '{service.process_name}'",
                shell=True,
                capture_output=True,
            )

            # Verify it's stopped
            import time

            time.sleep(1)
            status_after = ServiceManager.get_status(service_id)

            if not status_after["running"]:
                ram_freed = status.get("ram_mb", service.ram_mb or 0)
                logger.info("{} stopped (freed ~{} MB RAM)", service.name, ram_freed)
                return {
                    "success": True,
                    "message": f"{service.name} stopped",
                    "ram_freed_mb": round(ram_freed, 1),
                    "service_id": service_id,
                }
            else:
                return {
                    "success": False,
                    "error": f"Failed to stop {service.name}",
                }
        except Exception as e:
            logger.error("Error stopping {}: {}", service.name, e)
            return {
                "success": False,
                "error": str(e),
            }

    @staticmethod
    def restart(service_id: str) -> Dict:
        """Restart a service."""
        result_stop = ServiceManager.stop(service_id)
        if not result_stop.get("success"):
            return result_stop

        import time

        time.sleep(2)  # Wait before restarting

        return ServiceManager.start(service_id)


# Convenience functions
def get_service_status(service_id: str) -> Dict:
    """Get status of a service."""
    return ServiceManager.get_status(service_id)


def start_service(service_id: str) -> Dict:
    """Start a service."""
    return ServiceManager.start(service_id)


def stop_service(service_id: str) -> Dict:
    """Stop a service to free RAM."""
    return ServiceManager.stop(service_id)
