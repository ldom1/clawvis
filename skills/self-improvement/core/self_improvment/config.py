"""Configuration and API keys."""

from __future__ import annotations

import os
from pathlib import Path

HOME = Path.home()
_CORE_DIR = Path(__file__).resolve().parent.parent
_SKILL_ROOT = _CORE_DIR.parent


def _resolve_clawvis_root() -> Path | None:
    raw = os.getenv("CLAWVIS_ROOT", "").strip()
    if raw:
        p = Path(raw).expanduser().resolve()
        if (p / "hub-core").is_dir():
            return p
    for rel in (HOME / "lab" / "clawvis", HOME / "Lab" / "clawvis"):
        p = rel.resolve()
        if (p / "hub-core").is_dir():
            return p
    return None


def _bootstrap_dotenv() -> None:
    """Skill → core → repo `.env` (repo wins — same keys as agent-service)."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(_SKILL_ROOT / ".env", override=True)
    load_dotenv(_CORE_DIR / ".env", override=True)
    root = _resolve_clawvis_root()
    if root is not None and (root / ".env").is_file():
        load_dotenv(root / ".env", override=True)


_bootstrap_dotenv()

CLAWVIS_ROOT_PATH = _resolve_clawvis_root()

# cwd for review run: repo root when available (matches Clawvis layout), else skill root.
WORKSPACE = CLAWVIS_ROOT_PATH if CLAWVIS_ROOT_PATH is not None else _SKILL_ROOT

# Learnings always live next to this skill (repo: skills/self-improvement/.learnings).
LEARNINGS_DIR = _SKILL_ROOT / ".learnings"
MEMORY_FILE = WORKSPACE / "MEMORY.md"

# Lab trees (prefer lowercase linux/WSL convention).
LAB_ROOT = HOME / "lab"
LAB_ROOT_LEGACY = HOME / "Lab"

LOGGER_PACKAGE_CORE_PATH = (
    CLAWVIS_ROOT_PATH / "skills" / "logger" / "core"
    if CLAWVIS_ROOT_PATH is not None
    else None
)


def _s(x: str | None) -> str | None:
    """Strip key so CRLF/whitespace from .env don't cause 401."""
    return (x or "").strip() or None


# OpenRouter — aligned with agent-service / proactive-innovation
OPENROUTER_API_KEY = _s(os.getenv("OPENROUTER_API_KEY"))
OPENROUTER_BASE_URL = _s(os.getenv("OPENROUTER_BASE_URL")) or "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = _s(os.getenv("OPENROUTER_MODEL")) or "google/gemini-2.5-flash-lite"
