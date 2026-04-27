from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4

from loguru import logger

_INIT_LOCK = Lock()
_INITIALIZED = False
_LOG_PATH: Path | None = None


def _jsonl_sink(message) -> None:
    record = message.record
    payload = record.get("extra", {}).get("payload")
    if not isinstance(payload, dict):
        payload = {"message": str(record.get("message"))}
    if "level" not in payload:
        payload["level"] = record["level"].name
    if "ts" not in payload:
        payload["ts"] = datetime.now(UTC).isoformat() + "Z"
    path = _LOG_PATH or resolve_central_log_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(payload, ensure_ascii=False) + "\n")


def _repo_root() -> Path:
    # hub-core/hub_core/central_logger.py -> <repo>
    return Path(__file__).resolve().parents[2]


def resolve_central_log_file() -> Path:
    raw = os.environ.get("CENTRAL_LOG_FILE", "").strip()
    if raw:
        return Path(raw).expanduser()
    return _repo_root() / "logs" / "message-trajectory.jsonl"


def init_central_logger() -> Path:
    global _INITIALIZED, _LOG_PATH
    with _INIT_LOCK:
        path = resolve_central_log_file()
        if not _INITIALIZED:
            _LOG_PATH = path
            logger.add(_jsonl_sink, level="INFO", enqueue=True)
            _INITIALIZED = True
        return path


def get_component_logger(component: str):
    init_central_logger()
    return logger.bind(component=component)


def new_trace_id() -> str:
    return uuid4().hex


def trace_event(
    component: str,
    event: str,
    *,
    trace_id: str | None = None,
    level: str = "INFO",
    **meta: Any,
) -> dict[str, Any]:
    payload = {
        "ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "component": component,
        "event": event,
        "trace_id": trace_id or new_trace_id(),
        **meta,
    }
    init_central_logger()
    logger.bind(payload=payload).log(level.upper(), "trajectory")
    return payload
