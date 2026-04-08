"""Tests for hub_core.setup_sync."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from hub_core import setup_sync


def test_expected_skill_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "skills" / "x").mkdir(parents=True)
    monkeypatch.setenv("INSTANCE_NAME", "example")
    dirs = setup_sync.expected_skill_dirs(tmp_path, "example")
    assert len(dirs) == 1
    assert dirs[0] == str((tmp_path / "skills").resolve())


def test_sync_skills_openclaw_idempotent(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    cfg = tmp_path / "openclaw.json"
    cfg.write_text("{}", encoding="utf-8")
    (tmp_path / "skills").mkdir()
    monkeypatch.setenv("INSTANCE_NAME", "example")
    r1 = setup_sync.sync_skills_openclaw(
        tmp_path,
        openclaw_config=cfg,
    )
    assert r1.get("ok") is True
    assert r1.get("changed") is True
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["skills"]["load"]["extraDirs"]
    r2 = setup_sync.sync_skills_openclaw(tmp_path, openclaw_config=cfg)
    assert r2.get("changed") is False


def test_sync_skills_claude_symlink(tmp_path: Path) -> None:
    (tmp_path / "skills").mkdir()
    r = setup_sync.sync_skills_claude(tmp_path)
    assert r["ok"] is True
    link = tmp_path / ".claude" / "skills"
    assert link.is_symlink()
    assert link.resolve() == (tmp_path / "skills").resolve()


def test_sync_memory_openclaw(tmp_path: Path) -> None:
    ws = tmp_path / "ws"
    mem = tmp_path / "mem"
    mem.mkdir()
    r = setup_sync.sync_memory_openclaw(mem, workspace=ws)
    assert r["ok"] is True
    assert (ws / "memory").is_symlink()
    assert (ws / "MEMORY.md").exists()


def test_apply_localbrain_substitutions(tmp_path: Path) -> None:
    t = setup_sync.apply_localbrain_substitutions(
        "root={{MEMORY_ROOT_ABS}}",
        tmp_path,
    )
    assert str(tmp_path) in t


def test_setup_context_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "skills").mkdir()
    monkeypatch.setenv("INSTANCE_NAME", "example")
    monkeypatch.delenv("MEMORY_ROOT", raising=False)
    ctx = setup_sync.setup_context_payload(tmp_path)
    assert ctx["clawvis_root"] == str(tmp_path.resolve())
    assert "memory_root" in ctx
