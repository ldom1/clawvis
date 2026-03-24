"""Chat API — proxy to the configured AI runtime (Claude, Mistral, OpenClaw)."""

from __future__ import annotations

import os
from typing import AsyncIterator

import httpx
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter()


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    system: str = (
        "You are the Clawvis assistant. You help the user manage their projects, "
        "tasks, and knowledge base. Be concise and actionable."
    )


def _provider_config() -> dict:
    """Return active provider settings from environment."""
    provider = os.environ.get("PRIMARY_AI_PROVIDER", "claude").lower()
    return {
        "provider": provider,
        "claude_key": os.environ.get("CLAUDE_API_KEY", ""),
        "mistral_key": os.environ.get("MISTRAL_API_KEY", ""),
        "openclaw_url": os.environ.get("OPENCLAW_BASE_URL", "http://localhost:3333"),
        "openclaw_key": os.environ.get("OPENCLAW_API_KEY", ""),
    }


async def _stream_claude(req: ChatRequest, key: str) -> AsyncIterator[str]:
    messages = [{"role": m.role, "content": m.content} for m in req.history]
    messages.append({"role": "user", "content": req.message})
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "system": req.system,
        "messages": messages,
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json

                    try:
                        ev = json.loads(data)
                        if ev.get("type") == "content_block_delta":
                            delta = ev.get("delta", {})
                            text = delta.get("text", "")
                            if text:
                                yield text
                    except Exception:
                        pass


async def _stream_mistral(req: ChatRequest, key: str) -> AsyncIterator[str]:
    messages = [{"role": "system", "content": req.system}]
    for m in req.history:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": req.message})
    payload = {"model": "mistral-small-latest", "messages": messages, "stream": True}
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            "https://api.mistral.ai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "content-type": "application/json",
            },
            json=payload,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json

                    try:
                        ev = json.loads(data)
                        text = (
                            ev.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if text:
                            yield text
                    except Exception:
                        pass


async def _stream_openclaw(
    req: ChatRequest, url: str, key: str
) -> AsyncIterator[str]:
    messages = [{"role": "system", "content": req.system}]
    for m in req.history:
        messages.append({"role": m.role, "content": m.content})
    messages.append({"role": "user", "content": req.message})
    payload = {"model": "gpt-4o-mini", "messages": messages, "stream": True}
    headers = {"content-type": "application/json"}
    if key:
        headers["Authorization"] = f"Bearer {key}"
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            f"{url.rstrip('/')}/v1/chat/completions",
            headers=headers,
            json=payload,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    import json

                    try:
                        ev = json.loads(data)
                        text = (
                            ev.get("choices", [{}])[0]
                            .get("delta", {})
                            .get("content", "")
                        )
                        if text:
                            yield text
                    except Exception:
                        pass


@router.get("/chat/status")
def chat_status():
    """Return current provider config (keys masked)."""
    cfg = _provider_config()
    return {
        "provider": cfg["provider"],
        "claude_configured": bool(cfg["claude_key"]),
        "mistral_configured": bool(cfg["mistral_key"]),
        "openclaw_configured": bool(cfg["openclaw_url"])
        and cfg["openclaw_url"] != "http://localhost:3333",
    }


@router.post("/chat")
async def chat(req: ChatRequest):
    """Stream a chat response from the active AI provider."""
    cfg = _provider_config()
    provider = cfg["provider"]

    async def generate() -> AsyncIterator[str]:
        try:
            if provider == "claude" and cfg["claude_key"]:
                async for chunk in _stream_claude(req, cfg["claude_key"]):
                    yield chunk
            elif provider == "mistral" and cfg["mistral_key"]:
                async for chunk in _stream_mistral(req, cfg["mistral_key"]):
                    yield chunk
            elif provider == "openclaw":
                async for chunk in _stream_openclaw(
                    req, cfg["openclaw_url"], cfg["openclaw_key"]
                ):
                    yield chunk
            else:
                yield (
                    f"[No AI provider configured. Set {provider.upper()}_API_KEY in .env "
                    f"or configure via /settings/.]"
                )
        except httpx.HTTPStatusError as exc:
            yield f"[API error {exc.response.status_code}: {exc.response.text[:200]}]"
        except Exception as exc:
            yield f"[Error: {exc}]"

    return StreamingResponse(generate(), media_type="text/plain; charset=utf-8")
