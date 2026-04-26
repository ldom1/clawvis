"""Idempotent sync of Clawvis skills/memory with OpenClaw or Claude (.claude/)."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

import requests

from hub_core.config import OPENCLAW_CONFIG

_TEMPLATES = Path(__file__).resolve().parent / "templates"
_LOCALBRAIN_URL = (
    "https://raw.githubusercontent.com/ldom1/ai-dotfiles/main/.claude/LocalBrain.md"
)


def clawvis_root_from_env_or_file() -> Path:
    raw = os.environ.get("CLAWVIS_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    # hub-core/hub_core/setup_sync.py -> repo root
    return Path(__file__).resolve().parent.parent.parent


def resolve_memory_root(clawvis_root: Path) -> Path:
    mem = os.environ.get("MEMORY_ROOT")
    if mem:
        p = Path(mem).expanduser()
        if not p.is_absolute():
            p = clawvis_root / p
        return p.resolve()
    inst = os.environ.get("INSTANCE_NAME", "example")
    return (clawvis_root / "instances" / inst / "memory").resolve()


def instance_name() -> str:
    return os.environ.get("INSTANCE_NAME", "example").strip() or "example"


def _claude_host_config_dir_raw() -> str | None:
    """If set, all Claude Code files (claude.json, skills symlink, LocalBrain) use this dir.

    In Docker, bind-mount the host ``~/.claude`` here (e.g. ``/clawvis-host-claude``) so the
    API writes where Claude Code on the host reads — not the container home.
    """
    v = os.environ.get("CLAWVIS_HOST_CLAUDE_DIR", "").strip()
    return v or None


def claude_mcp_config_path() -> Path:
    h = _claude_host_config_dir_raw()
    if h:
        return Path(h).expanduser().resolve() / "claude.json"
    return Path.home() / ".claude" / "claude.json"


def claude_local_sync_dir(clawvis_root: Path) -> Path:
    """Directory for ``LocalBrain.md`` and the ``skills`` symlink."""
    h = _claude_host_config_dir_raw()
    if h:
        return Path(h).expanduser().resolve()
    return (clawvis_root / ".claude").resolve()


def claude_skills_symlink_target_abs(
    clawvis_root: Path,
    skills_resolved: Path,
) -> Path:
    """Absolute path stored in the symlink; must exist where Claude Code runs (usually host)."""
    host_repo = os.environ.get("CLAWVIS_REPO_HOST_PATH", "").strip()
    if not host_repo:
        return skills_resolved
    hr = Path(host_repo).expanduser().resolve()
    cr = clawvis_root.resolve()
    try:
        rel = skills_resolved.relative_to(cr)
    except ValueError:
        return skills_resolved
    return (hr / rel).resolve()


def mcp_server_js_for_claude_config(clawvis_root: Path) -> Path:
    """``claude.json`` MCP ``args`` path — must exist on the OS where Claude Code spawns ``node``."""
    o = os.environ.get("CLAWVIS_MCP_SERVER_JS", "").strip()
    if o:
        return Path(o).expanduser().resolve()
    hr = os.environ.get("CLAWVIS_REPO_HOST_PATH", "").strip()
    if hr:
        return (Path(hr).expanduser().resolve() / "mcp" / "server.js")
    return (clawvis_root / "mcp" / "server.js").resolve()


def expected_skill_dirs(clawvis_root: Path, inst: str) -> list[str]:
    dirs: list[str] = []
    core = clawvis_root / "skills"
    inst_sk = clawvis_root / "instances" / inst / "skills"
    if core.is_dir():
        dirs.append(str(core.resolve()))
    if inst_sk.is_dir():
        dirs.append(str(inst_sk.resolve()))
    if not dirs:
        raise ValueError(
            f"No skill directories found under {core} or {inst_sk}",
        )
    return dirs


def _patch_json_file(path: Path, mutator: Any) -> tuple[bool, dict[str, Any]]:
    if not path.exists():
        return False, {"ok": False, "error": f"Config not found: {path}"}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, {"ok": False, "error": f"Invalid JSON: {path}: {e}"}
    before = json.dumps(data, sort_keys=True)
    mutator(data)
    after = json.dumps(data, sort_keys=True)
    if before == after:
        return True, {"ok": True, "changed": False}
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return True, {"ok": True, "changed": True}


def sync_skills_openclaw(
    clawvis_root: Path,
    *,
    openclaw_config: Path | None = None,
    inst: str | None = None,
    extra_dirs: list[str] | None = None,
) -> dict[str, Any]:
    cfg = openclaw_config or OPENCLAW_CONFIG
    dirs = extra_dirs if extra_dirs is not None else expected_skill_dirs(
        clawvis_root,
        inst or instance_name(),
    )

    def mut(data: dict[str, Any]) -> None:
        skills = data.setdefault("skills", {})
        load = skills.setdefault("load", {})
        load["extraDirs"] = dirs

    ok, result = _patch_json_file(cfg, mut)
    if not ok:
        return result
    result["extraDirs"] = dirs
    result["openclaw_config"] = str(cfg)
    return result


def sync_skills_claude(
    clawvis_root: Path,
    *,
    skills_target: Path | None = None,
) -> dict[str, Any]:
    raw_target = skills_target or (clawvis_root / "skills")
    if not raw_target.is_dir():
        return {"ok": False, "error": f"Skills directory missing: {raw_target}"}
    target = raw_target.resolve()
    link_root = claude_local_sync_dir(clawvis_root)
    link_root.mkdir(parents=True, exist_ok=True)
    link = link_root / "skills"
    src = claude_skills_symlink_target_abs(clawvis_root, target)
    src_s = os.path.normpath(str(src))

    def _same_symlink() -> bool:
        if not link.is_symlink():
            return False
        try:
            cur = os.readlink(link)
        except OSError:
            return False
        if os.path.normpath(cur) == src_s:
            return True
        try:
            return Path(cur).expanduser().resolve() == src.resolve()
        except OSError:
            return False

    if link.is_symlink():
        if _same_symlink():
            return {
                "ok": True,
                "changed": False,
                "symlink": str(link),
                "target": src_s,
            }
        link.unlink()
    elif link.exists():
        return {
            "ok": False,
            "error": f"Path exists and is not a symlink: {link}",
        }
    os.symlink(src_s, link)
    return {"ok": True, "changed": True, "symlink": str(link), "target": src_s}


def sync_skills(
    provider: str,
    clawvis_root: Path | None = None,
    *,
    skills_path: str | None = None,
    openclaw_config: Path | None = None,
) -> dict[str, Any]:
    root = clawvis_root or clawvis_root_from_env_or_file()
    p = (provider or "").strip().lower()
    if p == "openclaw":
        extra = None
        if skills_path:
            extra = [str(Path(skills_path).expanduser().resolve())]
        return sync_skills_openclaw(
            root,
            openclaw_config=openclaw_config,
            extra_dirs=extra,
        )
    if p in ("claude", "anthropic"):
        st = Path(skills_path).expanduser().resolve() if skills_path else None
        return sync_skills_claude(root, skills_target=st)
    return {"ok": False, "error": f"Unknown provider: {provider}"}


def _memory_template_openclaw(memory_abs: Path) -> str:
    tpl = (_TEMPLATES / "MEMORY.openclaw.md").read_text(encoding="utf-8")
    return tpl.replace("{{MEMORY_ROOT_ABS}}", str(memory_abs))


def _fetch_localbrain_fallback() -> str:
    return (_TEMPLATES / "LocalBrain.md").read_text(encoding="utf-8")


def fetch_localbrain_text() -> str:
    try:
        r = requests.get(_LOCALBRAIN_URL, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception:
        return _fetch_localbrain_fallback()


def apply_localbrain_substitutions(text: str, memory_abs: Path) -> str:
    s = str(memory_abs)
    text = text.replace("{{MEMORY_ROOT_ABS}}", s)
    text = text.replace("{{MEMORY_ROOT}}", s)
    text = re.sub(
        r"(MEMORY_ROOT\s*=\s*)(\S+)",
        r"\g<1>" + s,
        text,
    )
    return text


def openclaw_workspace_path(override: Path | str | None) -> Path:
    if override is not None:
        return Path(str(override)).expanduser().resolve()
    return (
        Path(os.environ.get("OPENCLAW_WORKSPACE", str(Path.home() / ".openclaw" / "workspace")))
        .expanduser()
        .resolve()
    )


def sync_memory_openclaw(
    memory_root: Path,
    *,
    workspace: Path | None = None,
) -> dict[str, Any]:
    ws = openclaw_workspace_path(workspace)
    mem = memory_root.resolve()
    mem.mkdir(parents=True, exist_ok=True)
    link = ws / "memory"
    changed = False
    if link.is_symlink():
        if link.resolve() != mem:
            link.unlink()
            os.symlink(mem, link)
            changed = True
    elif link.exists():
        return {"ok": False, "error": f"memory path exists and is not a symlink: {link}"}
    else:
        ws.mkdir(parents=True, exist_ok=True)
        os.symlink(mem, link)
        changed = True
    md_path = ws / "MEMORY.md"
    content = _memory_template_openclaw(mem)
    if not md_path.exists() or md_path.read_text(encoding="utf-8") != content:
        md_path.write_text(content, encoding="utf-8")
        changed = True
    return {
        "ok": True,
        "changed": changed,
        "openclaw_workspace": str(ws),
        "memory_symlink": str(link),
        "memory_root": str(mem),
        "memory_md": str(md_path),
    }


def sync_memory_claude(
    clawvis_root: Path,
    memory_root: Path,
) -> dict[str, Any]:
    mem = memory_root.resolve()
    mem.mkdir(parents=True, exist_ok=True)
    out = claude_local_sync_dir(clawvis_root) / "LocalBrain.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = fetch_localbrain_text()
    content = apply_localbrain_substitutions(raw, mem)
    changed = True
    if out.exists() and out.read_text(encoding="utf-8") == content:
        changed = False
    else:
        out.write_text(content, encoding="utf-8")
    return {
        "ok": True,
        "changed": changed,
        "local_brain": str(out),
        "memory_root": str(mem),
    }


def sync_memory(
    provider: str,
    *,
    memory_root: Path | str | None = None,
    clawvis_root: Path | None = None,
    openclaw_workspace: Path | str | None = None,
) -> dict[str, Any]:
    root = clawvis_root or clawvis_root_from_env_or_file()
    mem = (
        Path(memory_root).expanduser().resolve()
        if memory_root
        else resolve_memory_root(root)
    )
    p = (provider or "").strip().lower()
    if p == "openclaw":
        return sync_memory_openclaw(mem, workspace=openclaw_workspace)
    if p in ("claude", "anthropic"):
        return sync_memory_claude(root, mem)
    return {"ok": False, "error": f"Unknown provider: {provider}"}


def _which_executable(name: str, path_env: str) -> str | None:
    """First match for `name` in path_env (os.pathsep-separated), executable only."""
    for directory in path_env.split(os.pathsep):
        directory = directory.strip()
        if not directory:
            continue
        candidate = Path(directory) / name
        try:
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate.resolve())
        except OSError:
            continue
    return None


def find_claude_on_path() -> str | None:
    """Return the absolute path to the claude CLI, or None if not found.

    Uses CLAUDE_CLI_PATH when set, then CLAWVIS_HOST_CLAUDE_CLI (host-mounted binary in
    Docker), then PATH / common dirs. The host CLI may exist but not be executable
    inside the container — a readable file at CLAWVIS_HOST_CLAUDE_CLI still counts.
    """
    explicit = os.environ.get("CLAUDE_CLI_PATH", "").strip()
    if explicit:
        p = Path(explicit).expanduser()
        try:
            if p.is_file() and os.access(p, os.X_OK):
                return str(p.resolve())
        except OSError:
            pass

    host_cli = os.environ.get("CLAWVIS_HOST_CLAUDE_CLI", "").strip()
    if host_cli:
        p = Path(host_cli).expanduser()
        try:
            if p.is_file():
                return str(p.resolve())
        except OSError:
            pass

    home = Path.home()
    extras = [
        str(home / ".local" / "bin"),
        str(home / "bin"),
        "/usr/local/bin",
        "/opt/homebrew/bin",
    ]
    base = os.environ.get("PATH", "")
    seen: set[str] = set()
    ordered: list[str] = []
    for d in (*extras, *base.split(os.pathsep)):
        d = d.strip()
        if not d or d in seen:
            continue
        seen.add(d)
        ordered.append(d)
    return _which_executable("claude", os.pathsep.join(ordered))


def get_skill_names(clawvis_root: Path) -> list[str]:
    """Discover all skill names from the skills directory."""
    skills_dir = clawvis_root / "skills"
    if not skills_dir.is_dir():
        return []
    return sorted(
        entry.name
        for entry in skills_dir.iterdir()
        if entry.is_dir() and not entry.name.startswith(".")
    )


def install_mcp_deps(clawvis_root: Path) -> dict[str, Any]:
    """Run ``npm install`` in ``mcp/`` if node_modules is absent or package.json changed.

    Safe to call from a container — the mcp/ dir is bind-mounted RW so the resulting
    node_modules lands on the host filesystem where Claude Code resolves imports.
    """
    mcp_dir = clawvis_root / "mcp"
    pkg = mcp_dir / "package.json"
    if not pkg.exists():
        return {"ok": False, "skipped": True, "reason": f"mcp/package.json not found: {mcp_dir}"}

    npm = shutil.which("npm")
    if not npm:
        return {"ok": False, "skipped": True, "reason": "npm not found on PATH"}

    node_modules = mcp_dir / "node_modules"
    if node_modules.is_dir():
        return {"ok": True, "skipped": True, "reason": "node_modules already present"}

    try:
        result = subprocess.run(
            [npm, "install", "--silent"],
            cwd=str(mcp_dir),
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return {
                "ok": False,
                "skipped": False,
                "reason": (result.stderr or result.stdout or "npm install failed").strip(),
            }
        return {"ok": True, "skipped": False, "mcp_dir": str(mcp_dir)}
    except Exception as exc:
        return {"ok": False, "skipped": False, "reason": str(exc)}


def sync_claude_code_mcp(clawvis_root: Path | None = None) -> dict[str, Any]:
    """Register Clawvis skills as an MCP server entry in claude.json.

    Writes under ``Path.home()/.claude`` locally, or ``CLAWVIS_HOST_CLAUDE_DIR`` when set
    (Docker: bind-mount host ``~/.claude`` there).

    Returns a result dict with keys: ok, skills_registered, mcp_config_path,
    changed, claude_available, and optionally error.
    """
    root = clawvis_root or clawvis_root_from_env_or_file()

    claude_bin = find_claude_on_path()
    # MCP registration runs `node` only; Claude Code resolves `claude` on the user's machine.
    # Do not fail the wizard when the API process has a stripped PATH (e.g. containers).

    skill_names = get_skill_names(root)

    config_path = claude_mcp_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        try:
            data: dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            return {
                "ok": False,
                "error": f"Invalid JSON in {config_path}: {e}",
                "claude_available": True,
            }
    else:
        data = {}

    mcp_servers: dict[str, Any] = data.setdefault("mcpServers", {})
    mcp_js = mcp_server_js_for_claude_config(root)

    mcp_servers["clawvis-skills"] = {
        "type": "stdio",
        "command": "node",
        "args": [str(mcp_js)],
    }

    config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    deps = install_mcp_deps(root)

    out: dict[str, Any] = {
        "ok": True,
        "skills_registered": skill_names,
        "skills_count": len(skill_names),
        "mcp_config_path": str(config_path),
        "mcp_server_path": str(mcp_js),
        "mcp_server_js": str(mcp_js),
        "claude_available": bool(claude_bin),
        "claude_cli_path": claude_bin or "",
        "mcp_deps": deps,
    }
    docker_host_mounted = bool(
        _claude_host_config_dir_raw() and os.environ.get("CLAWVIS_REPO_HOST_PATH", "").strip()
    )
    if not claude_bin and not docker_host_mounted:
        out["warning"] = (
            "Claude CLI not detected from this process. In Docker, mount the host binary and "
            "set CLAWVIS_HOST_CLAUDE_CLI (or CLAUDE_CLI_PATH). Mount host ~/.claude at "
            "CLAWVIS_HOST_CLAUDE_DIR so claude.json is written for Claude Code on the host."
        )
    return out


def setup_context_payload(clawvis_root: Path | None = None) -> dict[str, Any]:
    root = clawvis_root or clawvis_root_from_env_or_file()
    mem = resolve_memory_root(root)
    inst = instance_name()
    skills_core = root / "skills"
    skills_path = str(skills_core.resolve()) if skills_core.is_dir() else ""
    try:
        extra = expected_skill_dirs(root, inst)
    except ValueError:
        extra = []
    return {
        "clawvis_root": str(root),
        "instance_name": inst,
        "memory_root": str(mem),
        "skills_path": skills_path,
        "openclaw_extra_dirs_preview": extra,
        "openclaw_config": str(OPENCLAW_CONFIG),
        "openclaw_workspace_default": str(openclaw_workspace_path(None)),
        "openclaw_base_url": os.environ.get("OPENCLAW_BASE_URL", ""),
        "primary_ai_provider": os.environ.get("PRIMARY_AI_PROVIDER", ""),
        "claude_host_claude_dir": _claude_host_config_dir_raw() or "",
        "claude_repo_host_path": os.environ.get("CLAWVIS_REPO_HOST_PATH", "").strip(),
    }


def apply_sync_check(
    *,
    clawvis_root: Path | None = None,
) -> dict[str, Any]:
    """Run idempotent repairs for skills + memory (used by clawvis start)."""
    root = clawvis_root or clawvis_root_from_env_or_file()
    prov = (os.environ.get("PRIMARY_AI_PROVIDER") or "").strip().lower()
    out: dict[str, Any] = {"provider": prov, "actions": []}
    if prov == "openclaw":
        try:
            r = sync_skills("openclaw", root)
            if r.get("changed"):
                out["actions"].append({"skills": r})
        except Exception as e:
            out["actions"].append({"skills_error": str(e)})
        try:
            r = sync_memory("openclaw", clawvis_root=root)
            if r.get("changed"):
                out["actions"].append({"memory": r})
        except Exception as e:
            out["actions"].append({"memory_error": str(e)})
    elif prov in ("claude", "anthropic"):
        try:
            r = sync_skills("claude", root)
            if r.get("changed"):
                out["actions"].append({"skills": r})
        except Exception as e:
            out["actions"].append({"skills_error": str(e)})
        try:
            r = sync_memory("claude", clawvis_root=root)
            if r.get("changed"):
                out["actions"].append({"memory": r})
        except Exception as e:
            out["actions"].append({"memory_error": str(e)})
    return out
