"""List public skills/ directories (Clawvis repo)."""

from __future__ import annotations

from fastapi import APIRouter

from .core import _CLAWVIS_ROOT

router = APIRouter(tags=["skills"])


@router.get("/skills")
def list_clawvis_skills() -> dict:
    root = _CLAWVIS_ROOT / "skills"
    if not root.is_dir():
        return {"skills": []}
    names = sorted(
        p.name
        for p in root.iterdir()
        if p.is_dir() and not p.name.startswith(".")
    )
    return {"skills": [{"name": n} for n in names]}
