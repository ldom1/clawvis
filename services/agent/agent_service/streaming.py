from __future__ import annotations

import json
from typing import AsyncIterator

import httpx


async def stream_anthropic(
    message: str,
    history: list[dict],
    system: str,
    token: str,
    model: str = "claude-haiku-4-5",
) -> AsyncIterator[str]:
    messages = list(history) + [{"role": "user", "content": message}]
    payload = {
        "model": model,
        "max_tokens": 2048,
        "system": system,
        "messages": messages,
        "stream": True,
    }
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": token,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
        ) as resp:
            if not resp.is_success:
                await resp.aread()
                yield "[CLAWVIS:AUTH]" if resp.status_code == 401 else f"[CLAWVIS:HTTP:{resp.status_code}]"
                return
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    ev = json.loads(data)
                    if ev.get("type") == "content_block_delta":
                        text = ev.get("delta", {}).get("text", "")
                        if text:
                            yield text
                except Exception:
                    pass


async def stream_openai_compat(
    message: str,
    history: list[dict],
    system: str,
    token: str,
    base_url: str,
    model: str = "mistral-small-3.2-24b-instruct",
) -> AsyncIterator[str]:
    messages = [{"role": "system", "content": system}] + list(history) + [{"role": "user", "content": message}]
    payload = {"model": model, "messages": messages, "stream": True}
    async with httpx.AsyncClient(timeout=60) as client:
        async with client.stream(
            "POST",
            f"{base_url.rstrip('/')}/chat/completions",
            headers={
                "Authorization": f"Bearer {token}",
                "content-type": "application/json",
            },
            json=payload,
        ) as resp:
            if not resp.is_success:
                await resp.aread()
                yield "[CLAWVIS:AUTH]" if resp.status_code == 401 else f"[CLAWVIS:HTTP:{resp.status_code}]"
                return
            async for line in resp.aiter_lines():
                if not line.startswith("data: "):
                    continue
                data = line[6:]
                if data == "[DONE]":
                    break
                try:
                    ev = json.loads(data)
                    text = (ev.get("choices") or [{}])[0].get("delta", {}).get("content", "")
                    if text:
                        yield text
                except Exception:
                    pass
