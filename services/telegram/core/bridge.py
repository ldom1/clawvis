from __future__ import annotations

import httpx

from core.config import TelegramSettings
from core.models import AgentChatRequest

_AGENT_TIMEOUT_S = 120


class AgentError(Exception):
    pass


async def call_agent(
    settings: TelegramSettings,
    prompt: str,
    history: list | None = None,
) -> str:
    payload = AgentChatRequest(message=prompt, history=list(history or [])).model_dump()
    try:
        async with httpx.AsyncClient(timeout=_AGENT_TIMEOUT_S) as client:
            resp = await client.post(f"{settings.agent_url}/chat", json=payload)
            resp.raise_for_status()
            return resp.text
    except httpx.HTTPStatusError as exc:
        raise AgentError(f"HTTP {exc.response.status_code}: {exc.response.text}") from exc
    except httpx.RequestError as exc:
        raise AgentError(str(exc)) from exc
