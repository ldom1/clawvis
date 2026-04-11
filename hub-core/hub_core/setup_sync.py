"""Idempotent sync of Clawvis skills/memory with OpenClaw or Claude (.claude/)."""

from __future__ import annotations

import json
import os
import re
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
    target = skills_target or (clawvis_root / "skills")
    if not target.is_dir():
        return {"ok": False, "error": f"Skills directory missing: {target}"}
    target = target.resolve()
    link = clawvis_root / ".claude" / "skills"
    link.parent.mkdir(parents=True, exist_ok=True)
    if link.is_symlink():
        if link.resolve() == target:
            return {"ok": True, "changed": False, "symlink": str(link), "target": str(target)}
        link.unlink()
    elif link.exists():
        return {
            "ok": False,
            "error": f"Path exists and is not a symlink: {link}",
        }
    os.symlink(target, link)
    return {"ok": True, "changed": True, "symlink": str(link), "target": str(target)}


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
    out = clawvis_root / ".claude" / "LocalBrain.md"
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


def find_claude_on_path() -> str | None:
    """Return the absolute path to the claude CLI, or None if not found."""
    import shutil
    return shutil.which("claude")


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


def sync_claude_code_mcp(clawvis_root: Path | None = None) -> dict[str, Any]:
    """Register Clawvis skills as an MCP server entry in ~/.claude/claude.json.

    Returns a result dict with keys: ok, skills_registered, mcp_config_path,
    changed, claude_available, and optionally error.
    """
    root = clawvis_root or clawvis_root_from_env_or_file()

    claude_bin = find_claude_on_path()
    if not claude_bin:
        return {
            "ok": False,
            "error": "claude CLI not found on PATH",
            "claude_available": False,
        }

    skill_names = get_skill_names(root)

    config_path = Path.home() / ".claude" / "claude.json"
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
    mcp_server_path = root / "mcp" / "server.js"

    mcp_servers["clawvis-skills"] = {
        "type": "stdio",
        "command": "node",
        "args": [str(mcp_server_path)],
    }

    config_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")

    return {
        "ok": True,
        "skills_registered": skill_names,
        "skills_count": len(skill_names),
        "mcp_config_path": str(config_path),
        "mcp_server_path": str(mcp_server_path),
        "claude_cli_path": claude_bin,
    }


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
