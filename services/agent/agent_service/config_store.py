from __future__ import annotations

import json
import os
from pathlib import Path

_DEFAULTS: dict = {
    "preferred_provider": None,  # None = auto (anthropic first if available)
    "anthropic_model": "claude-haiku-4-5",
    # Default model id for the single OpenAI-compatible HTTP backend (OpenRouter, Mammouth, etc.).
    "mammouth_model": "qwen/qwen3-plus:free",
}

_ALLOWED = set(_DEFAULTS)


def _config_path() -> Path:
    if p := os.environ.get("AGENT_CONFIG_PATH"):
        return Path(p)
    return Path("/tmp/agent-config.json")


def load_config() -> dict:
    p = _config_path()
    if p.exists():
        try:
            return {**_DEFAULTS, **json.loads(p.read_text(encoding="utf-8"))}
        except Exception:
            pass
    return dict(_DEFAULTS)


def save_config(updates: dict) -> dict:
    current = load_config()
    for k, v in updates.items():
        if k in _ALLOWED:
            current[k] = v
    p = _config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(current, indent=2), encoding="utf-8")
    return current
