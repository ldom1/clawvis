from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from .config_store import load_config, save_config
from .openclaw_runner import (
    list_sessions,
    openclaw_available,
    restart_gateway,
    run_agent_session,
)
from .persona import load_persona
from .provider import ProviderConfig, load_provider_config
from .streaming import stream_anthropic, stream_openai_compat

router = APIRouter()


def primary_provider_from_env() -> str | None:
    """Hub UI: openclaw | claude if PRIMARY_AI_PROVIDER is set accordingly; else None."""
    raw = (os.environ.get("PRIMARY_AI_PROVIDER") or "").strip().lower()
    if raw == "openclaw":
        return "openclaw"
    if raw in ("claude", "anthropic"):
        return "claude"
    return None


def _normalize_provider_str(v: str) -> str:
    s = (v or "").strip().lower()
    if not s:
        return "anthropic"
    if s in ("anthropic", "claude"):
        return "anthropic"
    if s in ("mammouth", "mistral", "mammoth"):
        return "mammouth"
    if s in ("openclaw",):
        return "openclaw"
    return s


def effective_provider(conf: dict, cfg: ProviderConfig) -> str:
    if cfg.primary_from_env:
        return cfg.provider
    pp = conf.get("preferred_provider")
    if pp:
        return _normalize_provider_str(str(pp))
    return cfg.provider


def runtime_ready(cfg: ProviderConfig, eff: str) -> bool:
    if eff == "anthropic":
        return bool(cfg.anthropic_token)
    if eff == "mammouth":
        return bool(cfg.mammouth_token)
    if eff == "openclaw":
        return cfg.openclaw_available
    return False


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@router.get("/status")
def status():
    cfg = load_provider_config()
    conf = load_config()
    eff = effective_provider(conf, cfg)
    return {
        "provider": eff,
        "runtime_ready": runtime_ready(cfg, eff),
        "anthropic_configured": bool(cfg.anthropic_token),
        "mammouth_configured": bool(cfg.mammouth_token),
        "openclaw_available": cfg.openclaw_available,
        "primary_provider": primary_provider_from_env(),
    }


@router.get("/config")
def get_config():
    cfg = load_provider_config()
    conf = load_config()
    eff = effective_provider(conf, cfg)
    return {
        **conf,
        "anthropic_available": bool(cfg.anthropic_token),
        "mammouth_available": bool(cfg.mammouth_token),
        "openclaw_available": cfg.openclaw_available,
        "effective_provider": eff,
        "runtime_ready": runtime_ready(cfg, eff),
        "primary_from_env": cfg.primary_from_env,
        "primary_provider": primary_provider_from_env(),
    }


class AgentConfigUpdate(BaseModel):
    preferred_provider: str | None = None
    anthropic_model: str | None = None
    mammouth_model: str | None = None


@router.patch("/config")
def update_config(body: AgentConfigUpdate):
    updates: dict[str, Any] = {
        k: v for k, v in body.model_dump().items() if v is not None
    }
    # Allow explicitly setting preferred_provider to null via a separate mechanism;
    # for now a patch with None values is a no-op (fields not provided)
    saved = save_config(updates)
    return {"ok": True, "config": saved}


@router.post("/chat")
async def chat(req: ChatRequest):
    cfg = load_provider_config()
    conf = load_config()
    system = load_persona(cfg.openclaw_state_dir)

    preferred = effective_provider(conf, cfg)
    anthropic_model = conf.get("anthropic_model", "claude-haiku-4-5")
    mammouth_model = conf.get("mammouth_model", "mistral-small-3.2-24b-instruct")

    use_openclaw = preferred == "openclaw" and openclaw_available()
    use_anthropic = preferred == "anthropic" and bool(cfg.anthropic_token)
    use_mammouth = preferred == "mammouth" and bool(cfg.mammouth_token)

    async def generate():
        try:
            if use_openclaw:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: run_agent_session(req.message, local=True)
                )
                if result.success:
                    output = result.output
                    if isinstance(output, dict):
                        payloads = output.get("payloads") or []
                        text = " ".join(p.get("text", "") for p in payloads if p.get("text"))
                        if not text:
                            text = output.get("message", {}).get("content", "") or str(output)
                    else:
                        text = str(output)
                    yield text or "[OpenClaw: empty response]"
                else:
                    yield f"[OpenClaw error: {result.error}]"
            elif use_anthropic and cfg.anthropic_token:
                async for chunk in stream_anthropic(
                    req.message, req.history, system, cfg.anthropic_token,
                    model=anthropic_model,
                ):
                    yield chunk
            elif use_mammouth and cfg.mammouth_token:
                async for chunk in stream_openai_compat(
                    req.message, req.history, system,
                    cfg.mammouth_token, cfg.mammouth_base_url,
                    model=mammouth_model,
                ):
                    yield chunk
            else:
                yield (
                    "[No LLM provider configured. "
                    "Set ANTHROPIC_API_KEY or MAMMOUTH_API_KEY in .env]"
                )
        except Exception as exc:
            yield f"[Error: {type(exc).__name__}: {exc}]"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


class SessionRequest(BaseModel):
    message: str
    session_id: str | None = None
    local: bool = True


@router.post("/session")
def start_session(req: SessionRequest):
    if not openclaw_available():
        raise HTTPException(status_code=503, detail="OpenClaw not available")
    result = run_agent_session(req.message, req.session_id, local=req.local)
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return result.output


@router.get("/sessions")
def get_sessions():
    if not openclaw_available():
        raise HTTPException(status_code=503, detail="OpenClaw not available")
    result = list_sessions()
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return result.output


@router.post("/restart")
def restart():
    if not openclaw_available():
        raise HTTPException(status_code=503, detail="OpenClaw not available")
    result = restart_gateway()
    if not result.success:
        raise HTTPException(status_code=500, detail=result.error)
    return {"status": "restarted"}


@router.get("/cron")
def get_cron_jobs():
    """Return OpenClaw cron jobs from $OPENCLAW_STATE_DIR/cron/jobs.json."""
    state_dir = os.environ.get("OPENCLAW_STATE_DIR", "")
    if not state_dir:
        home = Path(os.environ.get("HOME", Path.home()))
        state_dir = str(home / ".openclaw")
    jobs_file = Path(state_dir) / "cron" / "jobs.json"
    if not jobs_file.exists():
        return {"jobs": [], "path": str(jobs_file), "found": False}
    try:
        data = json.loads(jobs_file.read_text(encoding="utf-8"))
        jobs = data if isinstance(data, list) else data.get("jobs", [])
        return {"jobs": jobs, "path": str(jobs_file), "found": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
