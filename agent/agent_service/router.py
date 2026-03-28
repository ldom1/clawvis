from __future__ import annotations

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
from .provider import load_provider_config
from .streaming import stream_anthropic, stream_openai_compat

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []


@router.get("/status")
def status():
    cfg = load_provider_config()
    conf = load_config()
    return {
        "provider": conf.get("preferred_provider") or cfg.provider,
        "anthropic_configured": bool(cfg.anthropic_token),
        "mammouth_configured": bool(cfg.mammouth_token),
        "openclaw_available": cfg.openclaw_available,
    }


@router.get("/config")
def get_config():
    cfg = load_provider_config()
    conf = load_config()
    return {
        **conf,
        "anthropic_available": bool(cfg.anthropic_token),
        "mammouth_available": bool(cfg.mammouth_token),
        "openclaw_available": cfg.openclaw_available,
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

    preferred = conf.get("preferred_provider")
    anthropic_model = conf.get("anthropic_model", "claude-haiku-4-5")
    mammouth_model = conf.get("mammouth_model", "mistral-small-3.2-24b-instruct")

    use_anthropic = (
        (preferred == "anthropic" and bool(cfg.anthropic_token))
        or (preferred is None and bool(cfg.anthropic_token))
        or (preferred == "mammouth" and not cfg.mammouth_token and bool(cfg.anthropic_token))
    )

    async def generate():
        try:
            if use_anthropic and cfg.anthropic_token:
                async for chunk in stream_anthropic(
                    req.message, req.history, system, cfg.anthropic_token,
                    model=anthropic_model,
                ):
                    yield chunk
            elif cfg.mammouth_token:
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
