from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from hub_core.central_logger import trace_event
from pydantic import BaseModel

from .cli_runner import CliRunner
from .config_store import load_settings, save_settings
from .orchestrate import _effective_provider as effective_provider, run_orchestrate_or_none
from .persona import load_persona
from .provider import ProviderConfig, load_provider_config, primary_ai_provider_raw
from .streaming import stream_anthropic, stream_openai_compat

_SCHEDULER_URL = os.environ.get("SCHEDULER_URL", "http://scheduler:8095")

router = APIRouter()


def _trace(event: str, *, trace_id: str | None = None, **meta: object) -> None:
    trace_event("agent.router", event, trace_id=trace_id, **meta)


def primary_provider_from_env() -> str | None:
    raw = primary_ai_provider_raw().strip().lower()
    if raw in ("cli", "claude-code", "opencode", "codex"):
        return "cli"
    if raw in ("anthropic", "claude"):
        return "anthropic"
    if raw in ("mammouth", "mistral", "openrouter"):
        return "mammouth"
    return None


def runtime_ready(cfg: ProviderConfig, eff: str) -> bool:
    if eff == "anthropic":
        return bool(cfg.anthropic_token)
    if eff == "mammouth":
        return bool(cfg.mammouth_token)
    if eff == "cli":
        return cfg.cli_available
    return False


def _lane_provider(conf: dict, cfg: ProviderConfig, key: str) -> str:
    lane = conf.get(key)
    if not lane:
        if key == "chat_preferred_provider":
            # Default chat lane: OpenRouter-compatible path when OPENROUTER token is configured.
            if bool(os.environ.get("OPENROUTER_API_KEY", "").strip()):
                lane = "mammouth"
            else:
                return effective_provider(conf, cfg)
        else:
            return effective_provider(conf, cfg)
    c = dict(conf)
    c["preferred_provider"] = lane
    return effective_provider(c, cfg)


def _provider_available(name: str, cfg: ProviderConfig) -> bool:
    if name == "cli":
        return cfg.cli_available
    if name == "anthropic":
        return bool(cfg.anthropic_token)
    if name == "mammouth":
        return bool(cfg.mammouth_token)
    return False


def _resolve_provider_for_chat(preferred: str, cfg: ProviderConfig) -> str:
    order = [preferred, "mammouth", "anthropic", "cli"]
    seen: set[str] = set()
    for p in order:
        if p in seen:
            continue
        seen.add(p)
        if _provider_available(p, cfg):
            return p
    return preferred


def _openai_compat_kind(base_url: str) -> str:
    u = (base_url or "").lower()
    if "openrouter.ai" in u or "/openrouter" in u:
        return "openrouter"
    if "mammouth" in u:
        return "mammouth"
    if "mistral" in u:
        return "mistral"
    if "generativelanguage" in u or "googleapis" in u:
        return "google"
    return "custom"


_OPENROUTER_DEFAULT_BASE = "https://openrouter.ai/api/v1"
_MAMMOUTH_DEFAULT_BASE = "https://api.mammouth.ai/v1"
_OPENROUTER_DEFAULT_MODEL = "qwen/qwen3-plus:free"
_MAMMOUTH_DEFAULT_MODEL = "mistral:mistral-small-3.2-24b-instruct"


def _providers_nested(cfg: ProviderConfig, conf: dict) -> dict[str, Any]:
    anthropic_model = conf.get("chat_model") or conf.get("task_preferred_model") or "claude-haiku-4-5"
    configured_model = conf.get("chat_model") or _OPENROUTER_DEFAULT_MODEL
    base = (cfg.mammouth_base_url or "").strip()
    kind = _openai_compat_kind(base)
    token_ok = bool(cfg.mammouth_token)

    openrouter_active = token_ok and kind in ("openrouter", "google", "custom")
    mammouth_active = token_ok and kind in ("mammouth", "mistral")

    return {
        "anthropic": {
            "label": "Anthropic (Claude API)",
            "available": bool(cfg.anthropic_token),
            "models": {"default": anthropic_model},
        },
        "openrouter": {
            "label": "OpenAI-compatible API",
            "kind": kind if openrouter_active else "openrouter",
            "available": openrouter_active,
            "base_url": base if openrouter_active else _OPENROUTER_DEFAULT_BASE,
            "models": {
                "default": configured_model if openrouter_active else _OPENROUTER_DEFAULT_MODEL
            },
            "note": (
                "Single token + base URL; qwen/qwen3-plus:free is the default model id "
                "for this endpoint."
            ),
        },
        "mammouth": {
            "label": "Mammouth (Mistral, etc.)",
            "base_url": base if mammouth_active else _MAMMOUTH_DEFAULT_BASE,
            "available": mammouth_active,
            "models": {
                "default": configured_model if mammouth_active else _MAMMOUTH_DEFAULT_MODEL
            },
            "note": (
                "Single token + base URL; mistral:mistral-small-3.2-24b-instruct is the "
                "default model id for this endpoint."
            ),
        },
        "cli": {
            "label": "CLI tool",
            "tool": cfg.cli_tool,
            "available": cfg.cli_available,
        },
    }


class ChatRequest(BaseModel):
    message: str
    history: list[dict] = []
    trace_id: str | None = None


@router.get("/status")
def status():
    cfg = load_provider_config()
    conf = load_settings()
    confd = conf.model_dump()
    eff = effective_provider(confd, cfg)
    return {
        "provider": eff,
        "runtime_ready": runtime_ready(cfg, eff),
        "anthropic_configured": bool(cfg.anthropic_token),
        "mammouth_configured": bool(cfg.mammouth_token),
        "cli_available": cfg.cli_available,
        "cli_tool": cfg.cli_tool,
        "primary_provider": primary_provider_from_env(),
    }


@router.get("/config")
def get_config():
    """Shape matches `docs/examples/agent-config-get-response.json` (Hub + docs)."""
    cfg = load_provider_config()
    conf = load_settings()
    confd = conf.model_dump()
    chat_lane = conf.chat_preferred_provider
    if not chat_lane and bool(os.environ.get("OPENROUTER_API_KEY", "").strip()):
        chat_lane = "mammouth"
    return {
        "preferred_provider": conf.preferred_provider,
        "chat_preferred_provider": chat_lane,
        "task_preferred_provider": conf.task_preferred_provider,
        "chat_model": conf.chat_model,
        "task_preferred_model": conf.task_preferred_model,
        "primary_provider": primary_provider_from_env(),
        "providers": _providers_nested(cfg, confd),
    }


class AgentConfigUpdate(BaseModel):
    preferred_provider: str | None = None
    chat_preferred_provider: str | None = None
    task_preferred_provider: str | None = None
    chat_model: str | None = None
    task_preferred_model: str | None = None


@router.patch("/config")
def update_config(body: AgentConfigUpdate):
    updates: dict[str, Any] = {
        k: v for k, v in body.model_dump().items() if v is not None
    }
    saved = save_settings(updates)
    return {"ok": True, "config": saved.model_dump()}


@router.post("/chat")
async def chat(req: ChatRequest):
    cfg = load_provider_config()
    conf = load_settings()
    confd = conf.model_dump()
    system = load_persona(None)

    preferred = _resolve_provider_for_chat(
        _lane_provider(confd, cfg, "chat_preferred_provider"), cfg
    )
    chat_model = conf.chat_model or "google/gemini-2.5-flash-lite"

    use_cli = preferred == "cli" and cfg.cli_available
    use_anthropic = preferred == "anthropic" and bool(cfg.anthropic_token)
    use_mammouth = preferred == "mammouth" and bool(cfg.mammouth_token)

    async def generate():
        try:
            _trace(
                "chat.received",
                trace_id=req.trace_id,
                message_chars=len(req.message or ""),
                history_len=len(req.history or []),
            )
            orch = await run_orchestrate_or_none(
                req.message,
                cfg,
                confd,
                system,
                "claude-haiku-4-5",
                "qwen/qwen3-plus:free",
                trace_id=req.trace_id,
            )
            if orch is not None:
                _trace("chat.orchestrated.reply", trace_id=req.trace_id, response_chars=len(orch or ""))
                yield orch
                return
            if use_cli:
                runner = CliRunner()
                try:
                    cli_model = chat_model if (chat_model or "").startswith("claude") else "claude-haiku-4-5"
                    text = await runner.run(req.message, model=cli_model)
                    _trace("chat.cli.reply", trace_id=req.trace_id, response_chars=len(text or ""))
                    yield text or "[CLI: empty response]"
                except TimeoutError as e:
                    _trace("chat.cli.timeout", trace_id=req.trace_id, error=str(e))
                    yield f"[CLI timeout: {e}]"
                except Exception as e:
                    _trace("chat.cli.error", trace_id=req.trace_id, error=str(e))
                    yield f"[CLI error: {e}]"
            elif use_anthropic and cfg.anthropic_token:
                async for chunk in stream_anthropic(
                    req.message, req.history, system, cfg.anthropic_token,
                    model=chat_model,
                ):
                    if chunk:
                        _trace("chat.anthropic.chunk", trace_id=req.trace_id, chunk_chars=len(chunk))
                    yield chunk
            elif use_mammouth and cfg.mammouth_token:
                async for chunk in stream_openai_compat(
                    req.message, req.history, system,
                    cfg.mammouth_token, cfg.mammouth_base_url,
                    model=chat_model,
                ):
                    if chunk:
                        _trace("chat.openrouter.chunk", trace_id=req.trace_id, chunk_chars=len(chunk))
                    yield chunk
            else:
                _trace("chat.no_provider", trace_id=req.trace_id)
                yield "[No LLM provider configured. Set ANTHROPIC_API_KEY or OPENROUTER_API_KEY in .env]"
        except Exception as exc:
            _trace("chat.error", trace_id=req.trace_id, error=f"{type(exc).__name__}: {exc}")
            yield f"[Error: {type(exc).__name__}: {exc}]"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")


# --- Cron / Scheduler proxy ---

async def _scheduler_request(method: str, path: str, body: dict | None = None) -> JSONResponse:
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            resp = await client.request(
                method,
                f"{_SCHEDULER_URL}{path}",
                json=body,
            )
        return JSONResponse(content=resp.json(), status_code=resp.status_code)
    except httpx.ConnectError:
        return JSONResponse({"ok": False, "error": "scheduler unavailable"}, status_code=503)
    except Exception as exc:
        return JSONResponse({"ok": False, "error": str(exc)}, status_code=502)


@router.get("/cron")
async def cron_list():
    return await _scheduler_request("GET", "/jobs")


class CronJobCreate(BaseModel):
    name: str
    cron: str
    prompt: str
    enabled: bool = True
    timezone: str = "UTC"


@router.post("/cron/jobs")
async def cron_create(body: CronJobCreate):
    return await _scheduler_request("POST", "/jobs", body.model_dump())


class CronJobPatch(BaseModel):
    cron: str | None = None
    prompt: str | None = None
    enabled: bool | None = None
    timezone: str | None = None


@router.patch("/cron/jobs/{name}")
async def cron_patch(name: str, body: CronJobPatch):
    return await _scheduler_request("PATCH", f"/jobs/{name}", body.model_dump(exclude_none=True))


@router.delete("/cron/jobs/{name}")
async def cron_delete(name: str):
    return await _scheduler_request("DELETE", f"/jobs/{name}")


@router.post("/cron/jobs/{name}/run")
async def cron_trigger(name: str):
    return await _scheduler_request("POST", f"/jobs/{name}/run")
