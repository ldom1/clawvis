"""Env config: load .env via python-dotenv without overriding existing vars."""

from __future__ import annotations

import json
from pathlib import Path

CHANNEL_STORE_PATH = Path(__file__).resolve().parents[1] / ".local" / "discord_channels.json"

DISCORD_CHANNEL_ENV_MAP = {
    "general": "DISCORD_CHANNEL_ID_GENERAL",
    "logs": "DISCORD_CHANNEL_ID_LOGS",
    "innovations": "DISCORD_CHANNEL_ID_INNOVATIONS",
    "projects": "DISCORD_CHANNEL_ID_PROJECTS",
    "ops": "DISCORD_CHANNEL_ID_OPS",
    "alerts": "DISCORD_CHANNEL_ID_ALERTS",
}


def load_env() -> None:
    """Load .env from skill core and package dirs; only set vars that are not already set."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    base = Path(__file__).resolve()
    for d in (base.parents[2], base.parents[1]):
        load_dotenv(d / ".env", override=False)


def get(key: str, default: str = "") -> str:
    """Return env var value (after load_env). Strips whitespace."""
    import os
    return os.environ.get(key, default).strip()


def get_discord_channel(name: str, default: str = "") -> str:
    """Return channel id by readable name (general, alerts, ops...)."""
    channel_name = name.strip().lower()
    key = DISCORD_CHANNEL_ENV_MAP.get(channel_name)
    if not key:
        return _get_channel_from_store(channel_name, default)
    value = get(key, "")
    if value:
        return value
    return _get_channel_from_store(channel_name, default)


def list_available_discord_channels() -> set[str]:
    names = set(DISCORD_CHANNEL_ENV_MAP)
    try:
        if CHANNEL_STORE_PATH.exists():
            data = json.loads(CHANNEL_STORE_PATH.read_text(encoding="utf-8"))
            channels = data.get("channels", {})
            if isinstance(channels, dict):
                names.update(str(k).strip().lower().replace("-", "_") for k in channels if str(k).strip())
    except (OSError, json.JSONDecodeError):
        pass
    return names


def _get_channel_from_store(name: str, default: str = "") -> str:
    try:
        if not CHANNEL_STORE_PATH.exists():
            return default
        data = json.loads(CHANNEL_STORE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default
    channels = data.get("channels", {})
    if not isinstance(channels, dict):
        return default
    channel = channels.get(name) or channels.get(name.replace("_", "-"))
    if isinstance(channel, str):
        return channel.strip()
    return default
