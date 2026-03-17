#!/usr/bin/env python3
"""
Unified system metrics: CPU, RAM, Disk.
Runs every 5 minutes via cron to keep metrics fresh.
"""

import json
from datetime import datetime

from loguru import logger

from hub_core.config import SYSTEM_JSON
from hub_core.models import CpuRam


def get_cpu_ram() -> CpuRam:
    """Get CPU and RAM usage."""
    try:
        with open("/proc/stat") as f:
            cpu_line = f.readline()

        with open("/proc/meminfo") as f:
            lines = f.readlines()

        cpu_data = list(map(int, cpu_line.split()[1:8]))
        cpu_total = sum(cpu_data)
        cpu_idle = cpu_data[3]
        cpu_percent = 100 * (1 - cpu_idle / cpu_total) if cpu_total > 0 else 0

        mem_dict = {
            line.split(":")[0].strip(): int(line.split(":")[1].split()[0])
            for line in lines
            if ":" in line
        }
        ram_total_kb = mem_dict.get("MemTotal", 0)
        ram_available_kb = mem_dict.get("MemAvailable", 0)
        ram_used_kb = ram_total_kb - ram_available_kb
        ram_total_gb = ram_total_kb / (1024 * 1024)
        ram_used_gb = ram_used_kb / (1024 * 1024)
        ram_percent = 100 * (ram_used_kb / ram_total_kb) if ram_total_kb > 0 else 0

        # Disk usage for root filesystem
        import os

        st = os.statvfs("/")
        disk_total = st.f_frsize * st.f_blocks
        disk_free = st.f_frsize * st.f_bavail
        disk_used = max(0, disk_total - disk_free)
        disk_percent = 100 * (disk_used / disk_total) if disk_total > 0 else 0

        return CpuRam(
            cpu_percent=round(cpu_percent, 1),
            ram_percent=round(ram_percent, 1),
            ram_used_gb=round(ram_used_gb, 2),
            ram_total_gb=round(ram_total_gb, 2),
            disk_percent=round(disk_percent, 1),
            disk_used_gb=round(disk_used / (1024 * 1024 * 1024), 2),
            disk_total_gb=round(disk_total / (1024 * 1024 * 1024), 2),
        )
    except Exception as e:
        logger.error("Error reading CPU/RAM: {}", e)
        return CpuRam()


def main():
    """Update CPU, RAM, Disk to system.json."""
    logger.info("Updating system metrics...")
    cpu_ram = get_cpu_ram()
    system_data = {
        **cpu_ram.model_dump(),
        "timestamp": datetime.now().isoformat(),
        "success": True,
    }
    SYSTEM_JSON.parent.mkdir(parents=True, exist_ok=True)
    with open(SYSTEM_JSON, "w") as f:
        json.dump(system_data, f, indent=2)
    logger.info("Metrics updated — CPU: {}% | RAM: {}% | Disk: {}%", cpu_ram.cpu_percent, cpu_ram.ram_percent, cpu_ram.disk_percent)


if __name__ == "__main__":
    main()
