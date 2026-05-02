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
    return cr if cr is not None else Path.home() / "lab" / "clawvis"


def memory_root() -> Path:
    m = os.environ.get("MEMORY_ROOT", "").strip()
    raw = os.environ.get("CLAWVIS_ROOT", "").strip()
    cr = Path(raw).expanduser().resolve() if raw else None
    if cr is None:
        for p in (Path.home() / "lab" / "clawvis", Path.home() / "Lab" / "clawvis"):
            if (p / "hub-core").is_dir():
                cr = p.resolve()
                break
    if m:
        p = Path(m).expanduser()
        if cr is not None and not p.is_absolute():
            p = cr / p
        return p.resolve()
    inst = os.environ.get("INSTANCE_NAME", "example").strip() or "example"
    if cr is not None:
        return (cr / "instances" / inst / "memory").resolve()
    return (Path.home() / "lab" / "clawvis" / "instances" / inst / "memory").resolve()
