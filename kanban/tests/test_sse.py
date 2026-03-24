"""SSE /stream — TestClient bloque sur les flux infinis ; on teste le contrat sans stream HTTP."""

from __future__ import annotations

import json

from kanban_api.server import app
from kanban_api.sse import _build_state


def test_openapi_stream_get():
    paths = app.openapi()["paths"]
    assert "/stream" in paths
    assert "get" in paths["/stream"]


def test_build_state_json_tasks_key():
    raw = _build_state()
    data = json.loads(raw)
    assert "tasks" in data
