"""One-shot (non-streaming) LLM completion for JSON planning."""
from __future__ import annotations

import httpx

from .cli_runner import CliRunner


async def complete_anthropic(
    system: str,
    user: str,
    token: str,
    model: str,
    max_tokens: int = 1024,
) -> str:
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": token,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json=payload,
        )
    if not resp.is_success:
        return f"[CLAWVIS:HTTP:{resp.status_code}]"
    data = resp.json()
    parts = data.get("content") or []
    out: list[str] = []
    for block in parts:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype == "text":
            out.append(str(block.get("text") or ""))
        # Some responses use tool_use or other blocks without text; skip for plan JSON
    text = "".join(out).strip()
    if not text and parts:
        return f"[CLAWVIS:empty-content:{data.get('stop_reason', 'unknown')}]"
    return text


async def complete_openai_compat(
    system: str,
    user: str,
    token: str,
    base_url: str,
    model: str,
    max_tokens: int = 1024,
) -> str:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
    }
    u = f"{base_url.rstrip('/')}/chat/completions"
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(
            u,
            headers={
                "Authorization": f"Bearer {token}",
                "content-type": "application/json",
            },
            json=payload,
        )
    if not resp.is_success:
        return f"[CLAWVIS:HTTP:{resp.status_code}]"
    data = resp.json()
    choice = (data.get("choices") or [{}])[0]
    msg = choice.get("message") or {}
    c = msg.get("content")
    if isinstance(c, list):
        # OpenAI / some OpenRouter shapes: list of {type, text} or strings
        pieces: list[str] = []
        for item in c:
            if isinstance(item, dict) and "text" in item:
                pieces.append(str(item.get("text") or ""))
            elif isinstance(item, str):
                pieces.append(item)
        return "".join(pieces).strip()
    if isinstance(c, str):
        return c.strip()
    if c is None:
        return ""
    return str(c).strip()


async def complete_cli(user: str, system: str, model: str | None = None) -> str:
    text = f"{system}\n\n---\n\n{user}"
    runner = CliRunner(timeout=120)
    try:
        return (await runner.run(text, model=model)) or ""
    except TimeoutError as e:
        return f"CLI timeout: {e}"
    except Exception as e:
        return f"CLI error: {e}"
