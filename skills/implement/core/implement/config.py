"""Configuration for implement."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

_skill_root = Path(__file__).parent.parent.parent
for _envf in (_skill_root / ".env", _skill_root / "core" / ".env"):
    if _envf.exists():
        load_dotenv(_envf, override=True)

KANBAN_API_URL: str = os.environ.get("KANBAN_API_URL", "http://localhost:8088/api/hub/kanban")

_memory_root = os.environ.get("MEMORY_ROOT") or str(Path.home() / ".openclaw" / "workspace" / "memory")
MEMORY_ROOT: Path = Path(_memory_root)
