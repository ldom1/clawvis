"""Tests for hub_core.setup_sync."""

from __future__ import annotations

import json
import os
import stat
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


def test_sync_skills_claude_symlink(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAWVIS_HOST_CLAUDE_DIR", raising=False)
    monkeypatch.delenv("CLAWVIS_REPO_HOST_PATH", raising=False)
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


def test_find_claude_on_path_home_local_bin(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    lb = tmp_path / ".local" / "bin"
    lb.mkdir(parents=True)
    fake = lb / "claude"
    fake.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    fake.chmod(fake.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", "/usr/bin")
    monkeypatch.delenv("CLAUDE_CLI_PATH", raising=False)
    monkeypatch.delenv("CLAWVIS_HOST_CLAUDE_CLI", raising=False)
    found = setup_sync.find_claude_on_path()
    assert found == str(fake.resolve())


def test_sync_claude_code_mcp_without_cli_on_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.delenv("CLAUDE_CLI_PATH", raising=False)
    monkeypatch.delenv("CLAWVIS_HOST_CLAUDE_DIR", raising=False)
    monkeypatch.delenv("CLAWVIS_HOST_CLAUDE_CLI", raising=False)
    monkeypatch.delenv("CLAWVIS_REPO_HOST_PATH", raising=False)
    monkeypatch.delenv("CLAWVIS_MCP_SERVER_JS", raising=False)
    (tmp_path / "skills" / "demo").mkdir(parents=True)
    (tmp_path / "mcp" / "server.js").parent.mkdir(parents=True)
    (tmp_path / "mcp" / "server.js").write_text("// stub\n", encoding="utf-8")
    r = setup_sync.sync_claude_code_mcp(tmp_path)
    assert r["ok"] is True
    assert r.get("claude_available") is False
    assert r.get("warning")
    cfg = tmp_path / ".claude" / "claude.json"
    assert cfg.is_file()
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert "clawvis-skills" in data.get("mcpServers", {})


def test_sync_claude_code_mcp_respects_host_claude_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    host = tmp_path / "host_claude"
    host.mkdir()
    monkeypatch.setenv("CLAWVIS_HOST_CLAUDE_DIR", str(host))
    monkeypatch.delenv("CLAUDE_CLI_PATH", raising=False)
    monkeypatch.delenv("CLAWVIS_HOST_CLAUDE_CLI", raising=False)
    monkeypatch.delenv("CLAWVIS_REPO_HOST_PATH", raising=False)
    monkeypatch.delenv("CLAWVIS_MCP_SERVER_JS", raising=False)
    (tmp_path / "skills" / "x").mkdir(parents=True)
    (tmp_path / "mcp" / "server.js").parent.mkdir(parents=True)
    (tmp_path / "mcp" / "server.js").write_text("//\n", encoding="utf-8")
    r = setup_sync.sync_claude_code_mcp(tmp_path)
    assert r["ok"] is True
    assert (host / "claude.json").is_file()


def test_sync_claude_code_mcp_uses_host_repo_for_mcp_js(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    host_repo = tmp_path / "on-host"
    (host_repo / "mcp" / "server.js").parent.mkdir(parents=True)
    (host_repo / "mcp" / "server.js").write_text("//\n", encoding="utf-8")
    ctr = tmp_path / "container"
    (ctr / "skills" / "a").mkdir(parents=True)
    (ctr / "mcp" / "server.js").parent.mkdir(parents=True)
    (ctr / "mcp" / "server.js").write_text("//\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("CLAWVIS_REPO_HOST_PATH", str(host_repo))
    monkeypatch.delenv("CLAWVIS_HOST_CLAUDE_DIR", raising=False)
    monkeypatch.delenv("CLAWVIS_MCP_SERVER_JS", raising=False)
    r = setup_sync.sync_claude_code_mcp(ctr)
    assert r["ok"] is True
    data = json.loads((tmp_path / ".claude" / "claude.json").read_text(encoding="utf-8"))
    arg0 = data["mcpServers"]["clawvis-skills"]["args"][0]
    assert arg0 == str((host_repo / "mcp" / "server.js").resolve())


def test_find_claude_on_path_host_cli_readable_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = tmp_path / "claude"
    fake.write_text("#not-executable\n", encoding="utf-8")
    monkeypatch.delenv("CLAUDE_CLI_PATH", raising=False)
    monkeypatch.setenv("CLAWVIS_HOST_CLAUDE_CLI", str(fake))
    found = setup_sync.find_claude_on_path()
    assert found == str(fake.resolve())


def test_install_mcp_deps_skips_when_node_modules_present(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mcp = tmp_path / "mcp"
    (mcp / "node_modules").mkdir(parents=True)
    (mcp / "package.json").write_text("{}", encoding="utf-8")
    r = setup_sync.install_mcp_deps(tmp_path)
    assert r["ok"] is True
    assert r["skipped"] is True


def test_install_mcp_deps_skips_when_no_package_json(tmp_path: Path) -> None:
    r = setup_sync.install_mcp_deps(tmp_path)
    assert r["ok"] is False
    assert r["skipped"] is True


def test_install_mcp_deps_skips_when_npm_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mcp = tmp_path / "mcp"
    mcp.mkdir()
    (mcp / "package.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("PATH", "")
    r = setup_sync.install_mcp_deps(tmp_path)
    assert r["ok"] is False
    assert r["skipped"] is True


def test_sync_claude_code_mcp_includes_mcp_deps(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("PATH", "/usr/bin:/bin")
    monkeypatch.delenv("CLAUDE_CLI_PATH", raising=False)
    monkeypatch.delenv("CLAWVIS_HOST_CLAUDE_DIR", raising=False)
    monkeypatch.delenv("CLAWVIS_HOST_CLAUDE_CLI", raising=False)
    monkeypatch.delenv("CLAWVIS_REPO_HOST_PATH", raising=False)
    monkeypatch.delenv("CLAWVIS_MCP_SERVER_JS", raising=False)
    (tmp_path / "skills" / "demo").mkdir(parents=True)
    (tmp_path / "mcp" / "server.js").parent.mkdir(parents=True)
    (tmp_path / "mcp" / "server.js").write_text("// stub\n", encoding="utf-8")
    r = setup_sync.sync_claude_code_mcp(tmp_path)
    assert r["ok"] is True
    assert "mcp_deps" in r
    deps = r["mcp_deps"]
    assert "ok" in deps


def test_sync_skills_claude_host_mount_symlink_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    host_claude = tmp_path / "hc"
    host_claude.mkdir()
    repo = tmp_path / "repo"
    skills = repo / "skills"
    skills.mkdir(parents=True)
    monkeypatch.setenv("CLAWVIS_HOST_CLAUDE_DIR", str(host_claude))
    monkeypatch.setenv("CLAWVIS_REPO_HOST_PATH", str(repo))
    r = setup_sync.sync_skills_claude(repo)
    assert r["ok"] is True
    link = host_claude / "skills"
    assert link.is_symlink()
    assert os.readlink(link) == str(skills.resolve())
