"""Tests for protocol_audit module."""

from __future__ import annotations

from pathlib import Path

from self_improvment.protocol_audit import (
    _check_pyproject,
    _read_text,
    _scan_skills,
    _worst_status,
    run_protocol_audit,
)


def test_read_text_exists(tmp_path: Path) -> None:
    f = tmp_path / "f.txt"
    f.write_text("hello world", encoding="utf-8")
    assert _read_text(f) == "hello world"
    assert _read_text(f, limit=5) == "hello"


def test_read_text_missing() -> None:
    assert _read_text(Path("/nonexistent/file")) == ""


def test_check_pyproject_ok(tmp_path: Path) -> None:
    p = tmp_path / "pyproject.toml"
    p.write_text("[project]\nname = 'x'\n[tool.uv]\n", encoding="utf-8")
    r = _check_pyproject(p)
    assert r["status"] == "OK"


def test_check_pyproject_no_uv(tmp_path: Path) -> None:
    p = tmp_path / "pyproject.toml"
    p.write_text("[project]\nname = 'x'\n", encoding="utf-8")
    r = _check_pyproject(p)
    assert r["status"] == "WARN"
    assert "uv" in str(r["notes"])


def test_worst_status() -> None:
    assert _worst_status([{"status": "OK"}]) == "OK"
    assert _worst_status([{"status": "WARN"}, {"status": "OK"}]) == "WARN"
    assert _worst_status([{"status": "OK"}, {"status": "FIXME"}]) == "FIXME"


def test_scan_skills_empty(monkeypatch: object) -> None:
    monkeypatch.setattr("self_improvment.protocol_audit.CLAWVIS_ROOT_PATH", None)
    assert _scan_skills() == []


def test_run_protocol_audit() -> None:
    status = run_protocol_audit()
    assert status in ("OK", "WARN", "FIXME")
    assert Path("/tmp/protocol-audit-report.md").exists()
