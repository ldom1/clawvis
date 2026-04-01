"""DomBot unified logger — writes to .log (text) and .jsonl (machine)."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any, cast

from loguru import logger as _loguru

from .models import LogEntry, LogLevel

LOG_DIR = Path.home() / ".openclaw" / "logs"
LOG_TEXT = LOG_DIR / "dombot.log"
LOG_JSONL = LOG_DIR / "dombot.jsonl"
DISCORD_SEND_SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "discord-send.sh"

_configured = False


def _ensure_configured():
    global _configured
    if _configured:
        return
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    _loguru.remove()
    _loguru.add(
        str(LOG_TEXT),
        format="{message}",
        rotation="10 MB",
        retention="30 days",
        compression="gz",
    )
    _configured = True


class DomBotLogger:
    def __init__(self, process: str = "agent:main", model: str = ""):
        self.process = process
        self.model = model

    def log(self, level: str, action: str, message: str, metadata: dict[str, Any] | None = None):
        entry = LogEntry(
            level=cast(LogLevel, level),
            process=self.process,
            model=self.model,
            action=action,
            message=message,
            metadata=metadata or {},
        )
        _write(entry)

    def info(self, action: str, message: str, **meta):
        self.log("INFO", action, message, meta)

    def warning(self, action: str, message: str, **meta):
        self.log("WARNING", action, message, meta)

    def error(self, action: str, message: str, **meta):
        self.log("ERROR", action, message, meta)

    def debug(self, action: str, message: str, **meta):
        self.log("DEBUG", action, message, meta)

    def critical(self, action: str, message: str, **meta):
        self.log("CRITICAL", action, message, meta)


def _write(entry: LogEntry):
    _ensure_configured()
    _loguru.info(entry.format_text())
    with open(LOG_JSONL, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry.model_dump(), ensure_ascii=False) + "\n")
    _send_to_discord(entry)


def _should_skip_discord(entry: LogEntry) -> bool:
    """Filtre le bruit : Discord = alertes, init projet, jalons — pas chaque INFO."""
    action = (entry.action or "").lower()
    msg = (entry.message or "").lower()
    level = (entry.level or "").upper()

    if level in {"ERROR", "CRITICAL"}:
        return False

    if level == "DEBUG":
        return True

    # Échecs explicites (même en WARN/INFO)
    if "fail" in action or "fail" in msg or "panic" in msg:
        return False

    # Jalons / init produit
    if "milestone" in action or "milestone" in msg:
        return False
    if "project" in action and any(x in action for x in ("init", "create", "archive")):
        return False
    if "project-init" in action or "sync:fail" == action:
        return False

    # Actions mail trop verboses
    if action.startswith("mail."):
        return True

    if action == "hub:refresh":
        return True

    if action == "cron:start":
        return True

    # Succès routiniers (backup, crons) — rester dans les fichiers logs Hub
    if action.endswith(":complete") or action in {"sync:complete"}:
        return True

    if level == "INFO":
        return True

    if level == "WARNING":
        return True

    return False


def _send_to_discord(entry: LogEntry) -> None:
    if not DISCORD_SEND_SCRIPT.exists():
        return
    if _should_skip_discord(entry):
        return
    target = _route_discord_channel(entry)
    if not target:
        return
    message = entry.format_human()
    try:
        subprocess.run(
            [str(DISCORD_SEND_SCRIPT), target, message],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        return


def _route_discord_channel(entry: LogEntry) -> str:
    level = (entry.level or "").upper()
    process = (entry.process or "").lower()
    action = (entry.action or "").lower()
    message = (entry.message or "").lower()
    meta_blob = json.dumps(entry.metadata or {}, ensure_ascii=False).lower()
    signal = f"{process} {action} {message} {meta_blob}"

    if level in {"ERROR", "CRITICAL"} or "fail" in signal or "panic" in signal:
        return "alerts"
    if "innov" in signal or "idea" in signal or "curiosity" in signal:
        return "innovations"
    if "project" in signal or "hub" in signal or "kanban" in signal:
        return "projects"
    if process.startswith("cron:") or process.startswith("system:") or process == "system":
        return "ops"
    return "logs"


def get_logger(process: str = "agent:main", model: str = "") -> DomBotLogger:
    return DomBotLogger(process=process, model=model)


def log(
    level: str = "INFO",
    process: str = "agent:main",
    model: str = "",
    action: str = "",
    message: str = "",
    metadata: dict[str, Any] | None = None,
):
    entry = LogEntry(
        level=cast(LogLevel, level),
        process=process,
        model=model,
        action=action,
        message=message,
        metadata=metadata or {},
    )
    _write(entry)


def _normalize_model(model: str) -> str:
    m = (model or "").strip()
    if not m:
        return ""
    lower = m.lower()
    if lower in {"haiku", "claude-haiku"}:
        return "anthropic/claude-haiku-4-5"
    if lower in {"claude-haiku-4-5", "anthropic/claude-haiku-4-5"}:
        return "anthropic/claude-haiku-4-5"
    return m


def get_logger_for_agent(
    model: str,
    *,
    subagent: str | None = None,
    channel: str | None = None,
) -> DomBotLogger:
    """
    Helper to get a logger with normalized process/model for agents.

    - Main agent: get_logger_for_agent("claude-haiku-4-5")
    - Subagent:   get_logger_for_agent("claude-haiku-4-5", subagent="curiosity")
    - Channel:    get_logger_for_agent("claude-haiku-4-5", channel="telegram")
    """
    norm_model = _normalize_model(model)
    if channel:
        process = f"channel:{channel}"
    elif subagent:
        process = f"subagent:{subagent}"
    else:
        process = "agent:main"
    return DomBotLogger(process=process, model=norm_model)
