import json
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from kanban_api.server import app

client = TestClient(app)


def test_sse_content_type():
    """GET /stream retourne 200 + text/event-stream."""
    with client.stream("GET", "/stream") as r:
        assert r.status_code == 200
        assert "text/event-stream" in r.headers["content-type"]


def test_sse_first_chunk_valid_json():
    """Le premier chunk data: contient un JSON valide avec clé 'tasks'."""
    # AsyncMock requis : asyncio.sleep est une coroutine, patch avec return_value=None lèverait TypeError
    with patch("kanban_api.sse.asyncio.sleep", new=AsyncMock(return_value=None)):
        with client.stream("GET", "/stream") as r:
            for i, line in enumerate(r.iter_lines()):
                if i > 50:
                    break  # garde-fou anti-boucle infinie
                if line.startswith("data:"):
                    payload = json.loads(line[5:].strip())
                    assert "tasks" in payload
                    break
