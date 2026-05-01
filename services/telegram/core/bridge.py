from __future__ import annotations

import httpx
from hub_core.central_logger import trace_event

from core.config import TelegramSettings
from core.models import AgentChatRequest

_AGENT_TIMEOUT_S = 120


class AgentError(Exception):
    pass


async def call_agent(
    settings: TelegramSettings,
    prompt: str,
    history: list | None = None,
    trace_id: str | None = None,
) -> str:
    payload = AgentChatRequest(message=prompt, history=list(history or [])).model_dump()
    if trace_id:
        payload["trace_id"] = trace_id
    trace_event(
        "telegram.bridge",
        "agent.request.start",
        trace_id=trace_id,
        prompt_chars=len(prompt),
        history_len=len(payload.get("history") or []),
    )
    try:
        async with httpx.AsyncClient(timeout=_AGENT_TIMEOUT_S) as client:
            resp = await client.post(f"{settings.agent_url}/chat", json=payload)
            resp.raise_for_status()
            trace_event(
                "telegram.bridge",
                "agent.request.ok",
                trace_id=trace_id,
                status_code=resp.status_code,
                response_chars=len(resp.text or ""),
            )
            return resp.text
    except httpx.HTTPStatusError as exc:
        trace_event(
            "telegram.bridge",
            "agent.request.http_error",
            trace_id=trace_id,
            status_code=exc.response.status_code,
        )
        raise AgentError(f"HTTP {exc.response.status_code}: {exc.response.text}") from exc
    except httpx.RequestError as exc:
        trace_event(
            "telegram.bridge",
            "agent.request.network_error",
            trace_id=trace_id,
            error=str(exc),
        )
        raise AgentError(str(exc)) from exc
