# services/agent/tests/test_provider.py
import pytest
from unittest.mock import patch


def test_fallback_to_env_anthropic(monkeypatch):
    monkeypatch.delenv("OPENCLAW_STATE_DIR", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    monkeypatch.delenv("MAMMOUTH_API_KEY", raising=False)

    from agent_service.provider import load_provider_config
    cfg = load_provider_config()
    assert cfg.provider == "anthropic"
    assert cfg.anthropic_token == "sk-ant-env"
    assert cfg.primary_from_env is False


def test_provider_is_mammouth_when_no_anthropic(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-openrouter")
    monkeypatch.delenv("OPENCLAW_STATE_DIR", raising=False)

    from agent_service.provider import load_provider_config
    cfg = load_provider_config()
    assert cfg.provider == "mammouth"
    assert cfg.mammouth_token == "sk-openrouter"


def test_primary_ai_provider_cli_overrides(monkeypatch):
    monkeypatch.setenv("PRIMARY_AI_PROVIDER", "cli")
    monkeypatch.setenv("CLI_TOOL", "claude")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    from agent_service.provider import load_provider_config
    cfg = load_provider_config()
    assert cfg.provider == "cli"
    assert cfg.primary_from_env is True


def test_primary_ai_provider_opencode_maps_to_cli(monkeypatch):
    monkeypatch.setenv("PRIMARY_AI_PROVIDER", "opencode")
    monkeypatch.setenv("CLI_TOOL", "opencode")

    from agent_service.provider import _normalize_primary_env
    assert _normalize_primary_env() == "cli"


def test_primary_ai_provider_from_dotenv_file(tmp_path, monkeypatch):
    envf = tmp_path / ".env"
    envf.write_text("PRIMARY_AI_PROVIDER=cli\n", encoding="utf-8")
    monkeypatch.setenv("CLAWVIS_DOTENV_PATH", str(envf))
    monkeypatch.delenv("PRIMARY_AI_PROVIDER", raising=False)

    from agent_service.provider import primary_ai_provider_raw
    assert primary_ai_provider_raw() == "cli"
