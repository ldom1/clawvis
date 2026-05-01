"""Shared fixtures: repo .env often sets PRIMARY_AI_PROVIDER=cli; tests need a neutral dotfile first."""

import pytest


@pytest.fixture
def neutral_primary_dotenv(tmp_path, monkeypatch):
    """Force `primary_ai_provider_raw()` to see an empty primary before any repo .env."""
    p = tmp_path / ".env"
    p.write_text("PRIMARY_AI_PROVIDER=\n", encoding="utf-8")
    monkeypatch.setenv("CLAWVIS_DOTENV_PATH", str(p))
