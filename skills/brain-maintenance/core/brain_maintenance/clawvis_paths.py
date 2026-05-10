"""Clawvis repo + memory roots from CLAWVIS_ROOT / MEMORY_ROOT."""

from __future__ import annotations

import os
from pathlib import Path


def clawvis_root() -> Path | None:
    raw = os.environ.get("CLAWVIS_ROOT", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    for p in (Path.home() / "lab" / "clawvis", Path.home() / "Lab" / "clawvis"):
        if (p / "hub-core").is_dir():
            return p.resolve()
    return None


def agent_workspace() -> Path:
    cr = clawvis_root()
    if cr:
        return cr
    return Path.home() / "lab" / "clawvis"


def brain_path() -> Path | None:
    """Resolve BRAIN_PATH from env or ~/ai-dotfiles/config/brain.env."""
    raw = os.environ.get("BRAIN_PATH", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    env_file = Path.home() / "ai-dotfiles" / "config" / "brain.env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("BRAIN_PATH="):
                val = line.split("=", 1)[1].strip().strip('"').strip("'")
                if val:
                    return Path(val).expanduser().resolve()
    return None


def memory_root() -> Path:
    m = os.environ.get("MEMORY_ROOT", "").strip()
    cr = clawvis_root()
    if m:
        p = Path(m).expanduser()
        if cr is not None and not p.is_absolute():
            p = cr / p
        return p.resolve()
    inst = os.environ.get("INSTANCE_NAME", "example").strip() or "example"
    if cr is not None:
        return (cr / "instances" / inst / "memory").resolve()
    return (Path.home() / "lab" / "clawvis" / "instances" / inst / "memory").resolve()
