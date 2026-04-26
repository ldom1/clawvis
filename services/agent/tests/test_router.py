# services/agent/tests/test_router.py
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch


@pytest.mark.asyncio
async def test_health():
    from agent_service.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_get_config_primary_provider_from_dotenv_file(tmp_path, monkeypatch):
    envf = tmp_path / ".env"
    envf.write_text("PRIMARY_AI_PROVIDER=cli\n", encoding="utf-8")
    monkeypatch.setenv("CLAWVIS_DOTENV_PATH", str(envf))
    monkeypatch.delenv("PRIMARY_AI_PROVIDER", raising=False)

    from agent_service.router import get_config
    body = get_config()
    assert set(body.keys()) == {"preferred_provider", "primary_provider", "providers"}
    assert body["primary_provider"] == "cli"
    prov = body["providers"]
    assert "cli" in prov
    assert "openrouter" in prov
    assert "openclaw" not in prov
    assert prov["openrouter"]["models"]["default"]
    assert prov["mammouth"]["models"]["default"]
    assert prov["openrouter"]["label"] == "OpenAI-compatible API"


def test_get_config_has_cli_provider(monkeypatch):
    monkeypatch.setenv("PRIMARY_AI_PROVIDER", "cli")
    monkeypatch.setenv("CLI_TOOL", "opencode")

    from agent_service.router import get_config
    body = get_config()
    assert "cli" in body["providers"]
    assert body["providers"]["cli"]["tool"] == "opencode"
    assert "openclaw" not in body["providers"]


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
    monkeypatch.delenv("PRIMARY_AI_PROVIDER", raising=False)
    monkeypatch.delenv("CLI_BIN", raising=False)

    from agent_service.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/chat", json={"message": "hi"})
    assert resp.status_code == 200
    assert "No LLM provider" in resp.text


@pytest.mark.asyncio
async def test_chat_uses_cli_runner(monkeypatch):
    monkeypatch.setenv("PRIMARY_AI_PROVIDER", "cli")
    monkeypatch.setenv("CLI_TOOL", "claude")

    async def fake_run(self, prompt):
        return "cli response"

    with patch("agent_service.cli_runner.CliRunner.run", fake_run):
        with patch("agent_service.cli_runner.CliRunner.available", return_value=True):
            from agent_service.main import app
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/chat", json={"message": "hi"})
    assert resp.status_code == 200
    assert "cli response" in resp.text
