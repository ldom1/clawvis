from __future__ import annotations

import httpx

from core.config import TelegramSettings


class AgentError(Exception):
    pass


async def call_agent(
    settings: TelegramSettings,
    prompt: str,
    history: list | None = None,
) -> str:
    payload = {"message": prompt, "history": history or []}
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(f"{settings.agent_url}/chat", json=payload)
            resp.raise_for_status()
            return resp.text
    except httpx.HTTPStatusError as exc:
        raise AgentError(f"HTTP {exc.response.status_code}") from exc
    except httpx.RequestError as exc:
        raise AgentError(str(exc)) from exc
