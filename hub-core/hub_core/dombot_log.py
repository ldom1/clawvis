"""DomBot structured log bridge for hub-core.

Writes to ~/.openclaw/logs/dombot.log (text) and dombot.jsonl (JSON),
using the same format as the dombot-logger skill so all agents share one log.

Usage:
    from hub_core.dombot_log import log, DomBotLog

    log("INFO", "hub-core:status", "system:refresh", "Hub state refreshed")

    with DomBotLog("hub-core:cron", model="claude-haiku-4-5") as dbl:
        dbl.info("task:start", "Starting provider fetch")
        dbl.info("task:complete", "Done", credits_available=42.5)
"""

from __future__ import annotations

import json
import os
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

LOG_DIR = Path.home() / ".openclaw" / "logs"
LOG_TEXT = LOG_DIR / "dombot.log"
LOG_JSONL = LOG_DIR / "dombot.jsonl"


def _write(level: str, process: str, model: str, action: str, message: str, metadata: dict) -> None:
    """Write one structured log entry to disk (dombot.log + dombot.jsonl)."""
    ts = datetime.now(UTC).isoformat() + "Z"
    entry = {
        "timestamp": ts,
        "level": level,
        "process": process,
        "model": model,
        "action": action,
        "message": message,
        "metadata": metadata,
        "pid": os.getpid(),
    }

    ts_short = ts[:19].replace("T", " ")
    meta_str = ""
    if metadata:
        meta_str = " (" + ", ".join(f"{k}={v}" for k, v in metadata.items()) + ")"
    text_line = (
        f"[{ts_short}] [{level:<8}] [{process}] [{model or '-'}] "
        f"{action} — {message}{meta_str}\n"
    )

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with open(LOG_TEXT, "a", encoding="utf-8") as f:
            f.write(text_line)
        with open(LOG_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Never crash the caller over logging


def log(level: str, process: str, action: str, message: str, model: str = "", **metadata: Any) -> None:
    """Write a single log entry."""
    _write(level, process, model, action, message, metadata)


class DomBotLog:
    """Structured logger bound to a process/model pair."""

    def __init__(self, process: str = "hub-core", model: str = ""):
        self.process = process
        self.model = model

    def info(self, action: str, message: str, **meta: Any) -> None:
        _write("INFO", self.process, self.model, action, message, meta)

    def warning(self, action: str, message: str, **meta: Any) -> None:
        _write("WARNING", self.process, self.model, action, message, meta)

    def error(self, action: str, message: str, **meta: Any) -> None:
        _write("ERROR", self.process, self.model, action, message, meta)

    def debug(self, action: str, message: str, **meta: Any) -> None:
        _write("DEBUG", self.process, self.model, action, message, meta)
