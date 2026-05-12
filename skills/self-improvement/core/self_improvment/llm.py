"""LLM calls via OpenRouter (same lane as agent-service)."""

from __future__ import annotations

from openai import OpenAI

from self_improvment.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    OPENROUTER_MODEL,
)
from self_improvment.logging import log_info, log_warning


def call_llm(prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        return (
            "ERROR: No API key (set OPENROUTER_API_KEY in Clawvis `.env` "
            "or skills/self-improvement `.env`)"
        )
    try:
        log_info("llm:try", "OpenRouter")
        client = OpenAI(api_key=OPENROUTER_API_KEY, base_url=OPENROUTER_BASE_URL)
        resp = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:  # pylint: disable=broad-exception-caught
        log_warning("llm:error", f"OpenRouter: {str(e)[:80]}")
        return f"ERROR: {e}"
