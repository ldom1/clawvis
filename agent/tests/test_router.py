# agent/tests/test_router.py
import pytest
from httpx import AsyncClient, ASGITransport


@pytest.mark.asyncio
async def test_health():
    from agent_service.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


import os
from unittest.mock import patch


@pytest.mark.asyncio
async def test_chat_returns_streaming_response(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("OPENCLAW_STATE_DIR", raising=False)

    async def fake_stream(*args, **kwargs):
        yield "Hello"
        yield " world"

    with patch("agent_service.router.stream_anthropic", side_effect=fake_stream):
        from agent_service.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/chat", json={"message": "hi"})
    assert resp.status_code == 200
    assert "Hello" in resp.text


@pytest.mark.asyncio
async def test_chat_no_provider_returns_error_message(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("MAMMOUTH_API_KEY", raising=False)
    monkeypatch.delenv("OPENCLAW_STATE_DIR", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from agent_service.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/chat", json={"message": "hi"})
    assert resp.status_code == 200
    assert "No LLM provider" in resp.text


@pytest.mark.asyncio
async def test_session_503_when_openclaw_unavailable(monkeypatch):
    monkeypatch.setenv("OPENCLAW_AVAILABLE", "false")
    from agent_service.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/session", json={"message": "run task"})
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_sessions_503_when_openclaw_unavailable(monkeypatch):
    monkeypatch.setenv("OPENCLAW_AVAILABLE", "false")
    from agent_service.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/sessions")
    assert resp.status_code == 503


@pytest.mark.asyncio
async def test_session_delegates_to_runner(monkeypatch):
    from agent_service import openclaw_runner
    from agent_service.openclaw_runner import OpenClawResult

    with patch("agent_service.router.openclaw_available", return_value=True), \
         patch("agent_service.router.run_agent_session",
               return_value=OpenClawResult(success=True, output={"reply": "done"})):
        from agent_service.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/session", json={"message": "run task"})
    assert resp.status_code == 200
    assert resp.json()["reply"] == "done"
