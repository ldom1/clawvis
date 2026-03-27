# agent/tests/test_persona.py
import pytest
from pathlib import Path


def _write_workspace(tmp_path, identity=None, soul=None):
    ws = tmp_path / "workspace"
    ws.mkdir()
    if identity:
        (ws / "IDENTITY.md").write_text(identity)
    if soul:
        (ws / "SOUL.md").write_text(soul)
    return str(tmp_path)


def test_loads_identity_and_soul(tmp_path):
    state_dir = _write_workspace(tmp_path, identity="# IDENTITY\nDomBot", soul="# SOUL\nSavant fou")
    from agent_service.persona import load_persona
    result = load_persona(state_dir)
    assert "IDENTITY" in result
    assert "SOUL" in result
    assert "---" in result


def test_fallback_when_no_state_dir():
    from agent_service.persona import load_persona
    result = load_persona(None)
    assert "Clawvis" in result
    assert len(result) > 20


def test_fallback_when_workspace_empty(tmp_path):
    (tmp_path / "workspace").mkdir()
    from agent_service.persona import load_persona
    result = load_persona(str(tmp_path))
    assert "Clawvis" in result
