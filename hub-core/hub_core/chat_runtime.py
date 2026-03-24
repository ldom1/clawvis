"""chat_runtime — streaming chat proxy for the active AI provider.

Logic lives here (hub-core); the HTTP router lives in kanban_api/chat_router.py.
"""

from __future__ import annotations

import json
import os
from typing import AsyncIterator

import httpx


def provider_config() -> dict:
    """Return active provider settings from environment."""
    provider = os.environ.get("PRIMARY_AI_PROVIDER", "claude").lower()
    return {
        "provider": provider,
        "claude_key": os.environ.get("CLAUDE_API_KEY", ""),
        "mistral_key": os.environ.get("MISTRAL_API_KEY", ""),
        "openclaw_url": os.environ.get(
            "OPENCLAW_BASE_URL", "http://localhost:3333"
        ),
        "openclaw_key": os.environ.get("OPENCLAW_API_KEY", ""),
    }


def provider_status() -> dict:
    cfg = provider_config()
    return {
        "provider": cfg["provider"],
        "claude_configured": bool(cfg["claude_key"]),
        "mistral_configured": bool(cfg["mistral_key"]),
        "openclaw_configured": bool(cfg["openclaw_url"])
        and cfg["openclaw_url"] != "http://localhost:3333",
    }


async def _sse_chunks(
    resp: httpx.Response, extract_text
) -> AsyncIterator[str]:
    """Parse SSE stream and extract text using the provided extractor."""
    async for line in resp.aiter_lines():
        if not line.startswith("data: "):
            continue
        data = line[6:]
        if data == "[DONE]":
            break
        try:
            ev = json.loads(data)
            text = extract_text(ev)
            if text:
                yield text
        except Exception:
            pass


async def stream_claude(
    message: str,
    history: list[dict],
    system: str,
    key: str,
) -> AsyncIterator[str]:
    messages = [{"role": m["role"], "content": m["content"]} for m in history]
    messages.append({"role": "user", "content": message})
    payload = {
        "model": "claude-sonnet-4-6",
        "max_tokens": 1024,
        "system": system,
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
            if not resp.is_success:
                body = await resp.aread()
                status = resp.status_code
                yield f"[API error {status}: {body.decode()[:200]}]"
                return
            async for chunk in _sse_chunks(
                resp,
                lambda ev: ev.get("delta", {}).get("text", "")
                if ev.get("type") == "content_block_delta"
                else "",
            ):
                yield chunk


async def stream_mistral(
    message: str,
    history: list[dict],
    system: str,
    key: str,
) -> AsyncIterator[str]:
    messages = [{"role": "system", "content": system}]
    messages.extend({"role": m["role"], "content": m["content"]} for m in history)
    messages.append({"role": "user", "content": message})
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
            if not resp.is_success:
                body = await resp.aread()
                yield f"[API error {resp.status_code}: {body.decode()[:200]}]"
                return
            async for chunk in _sse_chunks(
                resp,
                lambda ev: (ev.get("choices") or [{}])[0]
                .get("delta", {})
                .get("content", ""),
            ):
                yield chunk


async def stream_openclaw(
    message: str,
    history: list[dict],
    system: str,
    url: str,
    key: str,
) -> AsyncIterator[str]:
    messages = [{"role": "system", "content": system}]
    messages.extend({"role": m["role"], "content": m["content"]} for m in history)
    messages.append({"role": "user", "content": message})
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
            if not resp.is_success:
                body = await resp.aread()
                yield f"[API error {resp.status_code}: {body.decode()[:200]}]"
                return
            async for chunk in _sse_chunks(
                resp,
                lambda ev: (ev.get("choices") or [{}])[0]
                .get("delta", {})
                .get("content", ""),
            ):
                yield chunk


_DEFAULT_SYSTEM = (
    "You are the Clawvis assistant. You help the user manage their projects, "
    "tasks, and knowledge base. Be concise and actionable."
)


async def chat_stream(
    message: str,
    history: list[dict],
    system: str = _DEFAULT_SYSTEM,
) -> AsyncIterator[str]:
    """Entry point: route to the configured provider and stream text chunks."""
    cfg = provider_config()
    provider = cfg["provider"]
    try:
        if provider == "claude" and cfg["claude_key"]:
            async for chunk in stream_claude(
                message, history, system, cfg["claude_key"]
            ):
                yield chunk
        elif provider == "mistral" and cfg["mistral_key"]:
            async for chunk in stream_mistral(
                message, history, system, cfg["mistral_key"]
            ):
                yield chunk
        elif provider == "openclaw":
            async for chunk in stream_openclaw(
                message, history, system, cfg["openclaw_url"], cfg["openclaw_key"]
            ):
                yield chunk
        else:
            yield (
                f"[No AI provider configured. "
                f"Set {provider.upper()}_API_KEY in .env or configure via /settings/.]"
            )
    except httpx.ConnectError as exc:
        yield f"[Connection error: {exc}]"
    except Exception as exc:
        yield f"[Error: {type(exc).__name__}: {exc}]"
