"""Setup wizard API: sync skills and memory with OpenClaw or Claude."""

from __future__ import annotations

from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from hub_core.setup_sync import (
    setup_context_payload,
    sync_memory,
    sync_skills,
    sync_claude_code_mcp,
)

from .core import _CLAWVIS_ROOT

router = APIRouter(tags=["setup"])


def _upsert_env_key(env_path: Path, key: str, value: str) -> None:
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []
    prefix = f"{key}="
    out: list[str] = []
    replaced = False
    for line in lines:
        if line.startswith(prefix):
            out.append(f"{key}={value}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key}={value}")
    env_path.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")


class ProviderBody(BaseModel):
    provider: str


@router.post("/provider")
def post_setup_provider(body: ProviderBody) -> dict:
    """Set PRIMARY_AI_PROVIDER in repo .env (restart agent / stack to apply)."""
    if body.provider not in ("openclaw", "claude"):
        raise HTTPException(
            status_code=400,
            detail="provider must be openclaw or claude",
        )
    env_path = _CLAWVIS_ROOT / ".env"
    try:
        _upsert_env_key(env_path, "PRIMARY_AI_PROVIDER", body.provider)
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"ok": True, "PRIMARY_AI_PROVIDER": body.provider, "env_file": str(env_path)}


@router.get("/context")
def get_setup_context() -> dict:
    return setup_context_payload(_CLAWVIS_ROOT)


class SyncSkillsBody(BaseModel):
    provider: str = Field(..., description="openclaw or claude")
    skills_path: str | None = None


@router.post("/sync-skills")
def post_sync_skills(body: SyncSkillsBody) -> dict:
    try:
        out = sync_skills(
            body.provider,
            _CLAWVIS_ROOT,
            skills_path=body.skills_path,
        )
        if out.get("ok") is False:
            raise HTTPException(
                status_code=400,
                detail=out.get("error", "sync-skills failed"),
            )
        return out
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


class SyncMemoryBody(BaseModel):
    provider: str
    memory_root: str | None = None
    openclaw_workspace: str | None = None


@router.post("/sync-memory")
def post_sync_memory(body: SyncMemoryBody) -> dict:
    mem: Path | None = None
    if body.memory_root:
        mem = Path(body.memory_root).expanduser()
        if not mem.is_absolute():
            mem = (_CLAWVIS_ROOT / mem).resolve()
        else:
            mem = mem.resolve()
    try:
        out = sync_memory(
            body.provider,
            memory_root=mem,
            clawvis_root=_CLAWVIS_ROOT,
            openclaw_workspace=body.openclaw_workspace,
        )
        if out.get("ok") is False:
            raise HTTPException(
                status_code=400,
                detail=out.get("error", "sync-memory failed"),
            )
        return out
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except OSError as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/claude-code-sync")
def post_claude_code_sync() -> dict:
    """Register Clawvis skills as an MCP server entry in ~/.claude/claude.json."""
    try:
        out = sync_claude_code_mcp(_CLAWVIS_ROOT)
        if out.get("ok") is False:
            raise HTTPException(
                status_code=422,
                detail=out.get("error", "claude-code-sync failed"),
            )
        return out
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e

