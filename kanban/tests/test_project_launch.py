"""Tests for project launch resolution and build flow."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import kanban_api.core as core


def test_launch_status_uses_repo_dirname_and_projects_root(
    monkeypatch, tmp_path: Path
) -> None:
    projects_root = tmp_path / "projects"
    repo_dir = projects_root / "actual-app-dir"
    repo_dir.mkdir(parents=True)
    (repo_dir / "package.json").write_text(
        json.dumps({"scripts": {"build": "vite build"}}), encoding="utf-8"
    )
    (repo_dir / "index.html").write_text("<!doctype html>", encoding="utf-8")
    monkeypatch.setattr(
        core,
        "_find_project_or_raise",
        lambda _slug: {
            "slug": "logical-slug",
            "repo_path": str(repo_dir),
            "template": "frontend-vite",
        },
    )
    monkeypatch.setattr(
        core,
        "get_hub_settings",
        lambda: {
            "projects_root": str(projects_root),
            "instances_external_root": "",
            "linked_instances": [],
        },
    )

    status = core.get_project_launch_status("logical-slug")

    assert status["projects_root"] == str(projects_root)
    assert status["repo_in_projects_root"] is True
    assert status["app_slug"] == "actual-app-dir"
    assert status["launch_url"] == "/apps/actual-app-dir/"
    assert status["state"] == "buildable"
    assert status["reason"] == "build_required"


def test_build_project_and_launch_creates_dist_and_returns_launchable(
    monkeypatch, tmp_path: Path
) -> None:
    projects_root = tmp_path / "projects"
    repo_dir = projects_root / "vite-app"
    repo_dir.mkdir(parents=True)
    (repo_dir / "node_modules").mkdir()
    (repo_dir / "package.json").write_text(
        json.dumps({"scripts": {"build": "vite build"}}), encoding="utf-8"
    )
    (repo_dir / "index.html").write_text("<!doctype html>", encoding="utf-8")
    monkeypatch.setattr(
        core,
        "_find_project_or_raise",
        lambda _slug: {
            "slug": "demo",
            "repo_path": str(repo_dir),
            "template": "frontend-vite",
        },
    )
    monkeypatch.setattr(
        core,
        "get_hub_settings",
        lambda: {
            "projects_root": str(projects_root),
            "instances_external_root": "",
            "linked_instances": [],
        },
    )
    calls: list[list[str]] = []

    def fake_run(cmd, cwd, check, stdout, stderr, text, timeout):
        calls.append(cmd)
        assert Path(cwd) == repo_dir
        if cmd[:3] == ["npm", "run", "build"]:
            dist = repo_dir / "dist"
            dist.mkdir(exist_ok=True)
            (dist / "index.html").write_text("<!doctype html>", encoding="utf-8")
        return subprocess.CompletedProcess(cmd, 0, "", "")

    monkeypatch.setattr(core.subprocess, "run", fake_run)

    result = core.build_project_and_launch("demo")

    assert result["ok"] is True
    assert result["built"] is True
    assert result["launch_status"]["state"] == "launchable"
    assert result["launch_status"]["deployed_entry"] == "dist/index.html"
    assert calls == [["npm", "run", "build", "--", "--base=/apps/vite-app/"]]
