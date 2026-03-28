from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

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
    return {
        "provider": cfg.provider,
        "anthropic_configured": bool(cfg.anthropic_token),
        "mammouth_configured": bool(cfg.mammouth_token),
        "openclaw_available": cfg.openclaw_available,
    }


@router.post("/chat")
async def chat(req: ChatRequest):
    cfg = load_provider_config()
    system = load_persona(cfg.openclaw_state_dir)

    async def generate():
        try:
            if cfg.provider == "anthropic" and cfg.anthropic_token:
                async for chunk in stream_anthropic(
                    req.message, req.history, system, cfg.anthropic_token
                ):
                    yield chunk
            elif cfg.mammouth_token:
                async for chunk in stream_openai_compat(
                    req.message, req.history, system,
                    cfg.mammouth_token, cfg.mammouth_base_url,
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
