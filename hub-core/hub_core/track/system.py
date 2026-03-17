#!/usr/bin/env python3
"""
System resource tracking for Lab Hub.
Logs CPU and RAM usage to public API endpoint.
"""

import json
from datetime import datetime

import psutil
from loguru import logger

from hub_core.config import SYSTEM_JSON


def get_system_stats():
    """Get CPU and RAM usage via psutil or fallback."""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        ram_used_gb = ram.used / (1024**3)
        ram_total_gb = ram.total / (1024**3)

        return {
            "cpu_percent": round(cpu_percent, 1),
            "ram_percent": round(ram_percent, 1),
            "ram_used_gb": round(ram_used_gb, 2),
            "ram_total_gb": round(ram_total_gb, 2),
            "timestamp": datetime.now().isoformat(),
            "success": True,
        }
    except ImportError:
        # Fallback: simple estimation from /proc/
        try:
            # RAM usage (simple)
            with open("/proc/meminfo") as f:
                meminfo = {}
                for line in f:
                    key, val = line.split(":")
                    meminfo[key.strip()] = int(val.split()[0])

            ram_total_kb = meminfo.get("MemTotal", 0)
            ram_available_kb = meminfo.get("MemAvailable", 0)
            ram_used_kb = ram_total_kb - ram_available_kb
            ram_percent = (ram_used_kb / ram_total_kb * 100) if ram_total_kb > 0 else 0

            # CPU usage estimation (load average as proxy)
            with open("/proc/loadavg") as f:
                load_avg = float(f.read().split()[0])

            # Rough CPU% from load (1.0 = 1 core, assuming 4 cores)
            cpu_percent = min(load_avg * 25, 100)

            return {
                "cpu_percent": round(cpu_percent, 1),
                "ram_percent": round(ram_percent, 1),
                "ram_used_gb": round(ram_used_kb / (1024**2), 2),
                "ram_total_gb": round(ram_total_kb / (1024**2), 2),
                "timestamp": datetime.now().isoformat(),
                "success": True,
            }
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "success": False,
            }


def main():
    """Update system stats and write to API endpoint."""
    stats = get_system_stats()

    SYSTEM_JSON.parent.mkdir(parents=True, exist_ok=True)
    SYSTEM_JSON.write_text(json.dumps(stats, indent=2))

    if stats.get("success"):
        logger.info("{}", json.dumps(stats))
    else:
        logger.error("{}", json.dumps({"error": stats.get("error")}))

    return 0 if stats.get("success") else 1


if __name__ == "__main__":
    exit(main())
