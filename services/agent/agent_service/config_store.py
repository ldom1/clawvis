from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class AgentSettings(BaseModel):
    preferred_provider: str | None = None  # None = auto
    # Lane used for incoming chat requests (Telegram -> agent).
    # Provider default is resolved dynamically in router from token availability.
    chat_preferred_provider: str | None = None
    chat_model: str = "google/gemini-2.5-flash-lite"
    # Lane used for task orchestration/execution (agent -> run task).
    task_preferred_provider: str = "cli"
    task_preferred_model: str = "claude-haiku-4-5"


def _config_path() -> Path:
    if p := os.environ.get("AGENT_CONFIG_PATH"):
        return Path(p)
    return Path("/tmp/agent-config.json")


def load_settings() -> AgentSettings:
    p = _config_path()
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return AgentSettings.model_validate(data)
        except Exception:
            pass
    return AgentSettings()


def save_settings(updates: dict[str, Any]) -> AgentSettings:
    current = load_settings()
    merged = current.model_dump()
    allowed = set(AgentSettings.model_fields)
    for k, v in updates.items():
        if k in allowed:
            merged[k] = v
    next_settings = AgentSettings.model_validate(merged)
    p = _config_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(next_settings.model_dump(), indent=2), encoding="utf-8")
    return next_settings


def load_config() -> dict:
    return load_settings().model_dump()


def save_config(updates: dict[str, Any]) -> dict:
    return save_settings(updates).model_dump()
