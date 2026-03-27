# agent/tests/test_provider.py
import json
import os
import pytest
from pathlib import Path


def _write_profiles(tmp_path, anthropic_token, mammouth_token):
    profiles_dir = tmp_path / "agents" / "main" / "agent"
    profiles_dir.mkdir(parents=True)
    data = {
        "version": 1,
        "profiles": {
            "anthropic:default": {"type": "token", "provider": "anthropic", "token": anthropic_token},
            "mistral:default": {"type": "token", "provider": "mistral", "token": mammouth_token},
        },
    }
    (profiles_dir / "auth-profiles.json").write_text(json.dumps(data))


def test_load_from_profiles_file(tmp_path, monkeypatch):
    _write_profiles(tmp_path, "sk-ant-test", "sk-mammouth-test")
    monkeypatch.setenv("OPENCLAW_STATE_DIR", str(tmp_path))
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("MAMMOUTH_API_KEY", raising=False)

    from agent_service.provider import load_provider_config
    cfg = load_provider_config()
    assert cfg.anthropic_token == "sk-ant-test"
    assert cfg.mammouth_token == "sk-mammouth-test"
    assert cfg.provider == "anthropic"


def test_fallback_to_env(monkeypatch):
    monkeypatch.delenv("OPENCLAW_STATE_DIR", raising=False)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-env")
    monkeypatch.setenv("MAMMOUTH_API_KEY", "sk-mammouth-env")

    from agent_service.provider import load_provider_config
    cfg = load_provider_config()
    assert cfg.anthropic_token == "sk-ant-env"
    assert cfg.provider == "anthropic"


def test_provider_is_mistral_when_no_anthropic(monkeypatch):
    monkeypatch.delenv("OPENCLAW_STATE_DIR", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setenv("MAMMOUTH_API_KEY", "sk-mammouth-only")

    from agent_service.provider import load_provider_config
    cfg = load_provider_config()
    assert cfg.provider == "mistral"


def test_no_provider_gives_empty_tokens(monkeypatch):
    monkeypatch.delenv("OPENCLAW_STATE_DIR", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("MAMMOUTH_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    from agent_service.provider import load_provider_config
    cfg = load_provider_config()
    assert cfg.anthropic_token == ""
