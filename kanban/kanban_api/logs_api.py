"""Logs API router — reads ~/.openclaw/logs/dombot.jsonl with filters."""

from __future__ import annotations

import asyncio
import json
import os
from collections import Counter
from pathlib import Path

from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse

def _log_jsonl_path() -> Path:
    override = os.environ.get("DOMBOT_LOG_JSONL", "").strip()
    if override:
        return Path(override).expanduser()
    return Path.home() / ".openclaw" / "logs" / "dombot.jsonl"

router = APIRouter(prefix="/logs", tags=["logs"])


def _read_entries(
    level: str | None = None,
    process: str | None = None,
    action: str | None = None,
    search: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> list[dict]:
    log_jsonl = _log_jsonl_path()
    if not log_jsonl.exists():
        return []
    entries: list[dict] = []
    for line in log_jsonl.read_text(encoding="utf-8").strip().split("\n"):
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if level and e.get("level") != level.upper():
            continue
        if process and process not in e.get("process", ""):
            continue
        if action and action not in e.get("action", ""):
            continue
        if search and search.lower() not in json.dumps(e).lower():
            continue
        entries.append(e)
    entries.reverse()
    return entries[offset : offset + limit]


@router.get("")
def get_logs(
    level: str | None = Query(None),
    process: str | None = Query(None),
    action: str | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    try:
        entries = _read_entries(
            level=level,
            process=process,
            action=action,
            search=search,
            limit=limit,
            offset=offset,
        )
    except Exception:
        entries = []
    return {"logs": entries, "count": len(entries), "source_path": str(_log_jsonl_path())}


@router.get("/summary")
def get_logs_summary():
    log_jsonl = _log_jsonl_path()
    if not log_jsonl.exists():
        return {"total": 0, "by_level": {}, "by_process": {}, "recent_errors": []}
    lines = log_jsonl.read_text(encoding="utf-8").strip().split("\n")
    levels: Counter = Counter()
    processes: Counter = Counter()
    errors: list[dict] = []
    for line in lines:
        if not line.strip():
            continue
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        levels[e.get("level", "INFO")] += 1
        processes[e.get("process", "unknown")] += 1
        if e.get("level") in ("ERROR", "CRITICAL"):
            errors.append(e)
    return {
        "total": sum(levels.values()),
        "by_level": dict(levels),
        "by_process": dict(processes),
        "recent_errors": errors[-10:],
    }


@router.get("/stream")
async def stream_logs():
    async def event_generator():
        log_jsonl = _log_jsonl_path()
        if not log_jsonl.exists():
            return
        last_pos = log_jsonl.stat().st_size
        while True:
            await asyncio.sleep(2)
            log_jsonl = _log_jsonl_path()
            if not log_jsonl.exists():
                continue
            size = log_jsonl.stat().st_size
            if size <= last_pos:
                continue
            with open(log_jsonl, "r", encoding="utf-8") as f:
                f.seek(last_pos)
                new_data = f.read()
                last_pos = f.tell()
            for line in new_data.strip().split("\n"):
                if line.strip():
                    yield f"data: {line}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
