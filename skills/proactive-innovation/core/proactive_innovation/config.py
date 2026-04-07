"""Paths and limits. No Telegram/API calls here."""

from __future__ import annotations

import json
import os
from pathlib import Path

# Load .env from skill root then core/ (core wins). override=True so .env beats openclaw.json.
try:
    from dotenv import load_dotenv
    _core_dir = Path(__file__).resolve().parent.parent
    load_dotenv(_core_dir.parent / ".env", override=True)
    load_dotenv(_core_dir / ".env", override=True)
except ImportError:
    pass

HOME = Path.home()
WORKSPACE = HOME / ".openclaw" / "workspace"
MEMORY = WORKSPACE / "memory"
PROJECTS_DIR = MEMORY / "projects"
KNOWLEDGE_DIR = MEMORY / "resources" / "knowledge"
CURIOSITY_DIR = MEMORY / "resources" / "curiosity"
ENTREPRENEUR_FILE = MEMORY / "caps" / "entrepreneur.md"
IDEAS_DIR = MEMORY / "resources" / "ideas"

# Guardrails: prevent runaway loops
MAX_PROJECTS_PER_RUN = 10
MAX_IMPROVEMENTS_PER_PROJECT = 5
MAX_IDEAS_PER_RUN = 3
SECTION_HEADER = "## Améliorations proposées (auto)"
IDEA_SECTION_HEADER = "## Idées (propositions auto)"
TIMELINE_HEADER = "## Timeline"


def _s(x: str | None) -> str | None:
    """Strip key so CRLF/whitespace from .env don't cause 401."""
    return (x or "").strip() or None


def load_openrouter_key() -> str | None:
    k = _s(os.getenv("OPENROUTER_API_KEY"))
    if k:
        return k
    try:
        path = HOME / ".openclaw" / "openclaw.json"
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
        entries = cfg.get("skills", {}).get("entries", {})
        for name in ("proactive-innovation", "self-improving-agent", "self-improvement"):
            env = (entries.get(name) or {}).get("env") or {}
            k = _s(env.get("OPENROUTER_API_KEY"))
            if k:
                return k
        return _s(cfg.get("env", {}).get("OPENROUTER_API_KEY"))
    except (json.JSONDecodeError, OSError, TypeError):
        return None


def load_openrouter_model() -> str:
    return _s(os.getenv("OPENROUTER_MODEL")) or "google/gemini-2.5-flash-lite"


OPENROUTER_API_KEY = load_openrouter_key()
OPENROUTER_MODEL = load_openrouter_model()
