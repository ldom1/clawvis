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
    assert {
        "preferred_provider",
        "chat_preferred_provider",
        "task_preferred_provider",
        "chat_model",
        "task_preferred_model",
        "primary_provider",
        "providers",
    }.issubset(set(body.keys()))
    assert body["primary_provider"] == "cli"
    assert body["chat_preferred_provider"] in (None, "mammouth")
    assert body["task_preferred_provider"] == "cli"
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


def test_get_config_chat_lane_defaults_to_openrouter_when_key_set(monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-openrouter")
    monkeypatch.delenv("PRIMARY_AI_PROVIDER", raising=False)
    monkeypatch.delenv("CLAWVIS_DOTENV_PATH", raising=False)

    from agent_service.router import get_config

    body = get_config()
    assert body["chat_preferred_provider"] == "mammouth"


@pytest.mark.asyncio
async def test_chat_returns_streaming_response(monkeypatch, neutral_primary_dotenv):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("OPENCLAW_STATE_DIR", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

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
async def test_chat_no_provider_returns_error_message(monkeypatch, neutral_primary_dotenv):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("MAMMOUTH_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("OPENCLAW_STATE_DIR", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("CLI_BIN", raising=False)

    from agent_service.main import app
    with patch("agent_service.cli_runner.CliRunner.available", return_value=False):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post("/chat", json={"message": "hi"})
    assert resp.status_code == 200
    assert "No LLM provider" in resp.text


@pytest.mark.asyncio
async def test_chat_orchestration_short_circuits_response(monkeypatch, neutral_primary_dotenv):
    """Task-shaped messages are handled by orchestration before the generic LLM path."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    async def fake_orch(*_a, **_k):
        return "Created task t-abc: My title (project: my-proj)"
    with patch("agent_service.router.run_orchestrate_or_none", side_effect=fake_orch):
        from agent_service.main import app
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            resp = await client.post(
                "/chat",
                json={"message": "Create a new task in project X: do the thing"},
            )
    assert resp.status_code == 200
    assert "Created task t-abc" in resp.text
    assert "my-proj" in resp.text


@pytest.mark.asyncio
async def test_chat_uses_cli_runner(monkeypatch, tmp_path):
    envf = tmp_path / ".env"
    envf.write_text("PRIMARY_AI_PROVIDER=cli\n", encoding="utf-8")
    monkeypatch.setenv("CLAWVIS_DOTENV_PATH", str(envf))
    monkeypatch.setenv("CLI_TOOL", "claude")

    async def fake_run(self, prompt, model=None):
        return "cli response"

    with patch("agent_service.cli_runner.CliRunner.run", fake_run):
        with patch("agent_service.cli_runner.CliRunner.available", return_value=True):
            from agent_service.main import app
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                resp = await client.post("/chat", json={"message": "hi"})
    assert resp.status_code == 200
    assert "cli response" in resp.text
