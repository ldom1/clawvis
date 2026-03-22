"""Configuration for kanban-implementer."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from skill root or core
_skill_root = Path(__file__).parent.parent.parent
for _envf in (_skill_root / ".env", _skill_root / "core" / ".env"):
    if _envf.exists():
        load_dotenv(_envf, override=True)

WORKSPACE = Path.home() / ".openclaw" / "workspace"
TASKS_JSON = WORKSPACE / "memory" / "kanban" / "tasks.json"
LAB = Path.home() / "Lab"
PROTOCOL_MD = LAB / "PROTOCOL.md"

# Project to prioritize (overrides priority sorting for tasks in this project)
PRIORITY_PROJECT: str | None = os.environ.get("KANBAN_PRIORITY_PROJECT") or None

# Max effort_hours to auto-pick (avoid multi-day tasks)
MAX_EFFORT: float = float(os.environ.get("KANBAN_MAX_EFFORT", "2.0"))

# Minimum confidence score (Kahneman) — tasks below are skipped
# null treated as 0.5; human assignee always gets 1.0
MIN_CONFIDENCE: float = float(os.environ.get("KANBAN_MIN_CONFIDENCE", "0.4"))

# Kanban API base (local hub)
KANBAN_API = os.environ.get("KANBAN_API_URL", "http://localhost:8088/api/kanban")

TELEGRAM_TARGET = "5689694685"
