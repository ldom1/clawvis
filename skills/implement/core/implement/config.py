"""Configuration for implement."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from implement.clawvis_paths import agent_workspace, memory_root as _resolved_memory_root

_skill_root = Path(__file__).parent.parent.parent
for _envf in (_skill_root / ".env", _skill_root / "core" / ".env"):
    if _envf.exists():
        load_dotenv(_envf, override=True)

KANBAN_API_URL: str = os.environ.get("KANBAN_API_URL", "http://localhost:8088/api/hub/kanban")

MEMORY_ROOT: Path = _resolved_memory_root()
WORKSPACE: Path = agent_workspace()
TASKS_JSON: Path = MEMORY_ROOT / "kanban" / "tasks.json"

PRIORITY_PROJECT: str | None = os.environ.get("KANBAN_PRIORITY_PROJECT") or None
MAX_EFFORT: float = float(os.environ.get("KANBAN_MAX_EFFORT", "2.0"))
MIN_CONFIDENCE: float = float(os.environ.get("KANBAN_MIN_CONFIDENCE", "0.4"))
