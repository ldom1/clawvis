"""SSE endpoint — live kanban stream with hash-based deduplication."""

import asyncio
import hashlib
import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from .core import list_active_tasks

router = APIRouter()


def _build_state() -> str:
    """Serialize kanban state. sort_keys=True ensures hash stability."""
    try:
        data = list_active_tasks()
    except FileNotFoundError:
        data = {"tasks": [], "stats": {}, "projects": [], "meta": {}}
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


@router.get("/stream")
async def stream_kanban():
    """SSE endpoint: push full state on change, heartbeat otherwise."""

    async def event_generator():
        yield ": ping\n\n"
        last_hash = ""
        while True:
            await asyncio.sleep(5)
            current = _build_state()
            h = hashlib.md5(current.encode()).hexdigest()
            if h != last_hash:
                last_hash = h
                yield f"data: {current}\n\n"
            else:
                yield ": ping\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
