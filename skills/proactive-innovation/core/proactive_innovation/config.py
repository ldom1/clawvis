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


def load_api_keys() -> tuple[str | None, str | None]:
    """Load API keys from env or openclaw.json. Env (e.g. from .env) wins."""
    claude_key = _s(os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY"))
    mammouth_key = _s(os.getenv("MAMMOUTH_API_KEY") or os.getenv("MISTRAL_API_KEY"))
    if claude_key and mammouth_key:
        return claude_key, mammouth_key
    try:
        config_file = HOME / ".openclaw" / "openclaw.json"
        if config_file.exists():
            with open(config_file, encoding="utf-8") as f:
                config = json.load(f)
            skills = config.get("skills", {})
            entries = skills.get("entries", {})
            self_imp = entries.get("self-improvement") or entries.get("proactive-innovation") or skills.get("self-improvement") or skills.get("proactive-innovation") or {}
            env = self_imp.get("env", {})
            if env:
                claude_key = claude_key or _s(env.get("ANTHROPIC_API_KEY") or env.get("CLAUDE_API_KEY"))
                mammouth_key = mammouth_key or _s(env.get("MAMMOUTH_API_KEY") or env.get("MISTRAL_API_KEY"))
    except (json.JSONDecodeError, OSError):
        pass
    return claude_key, mammouth_key


CLAUDE_API_KEY, MAMMOUTH_API_KEY = load_api_keys()
