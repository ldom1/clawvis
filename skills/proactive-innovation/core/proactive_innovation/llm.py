"""LLM calls via OpenRouter (OpenAI-compatible). Used at most twice per run (improvements + ideas)."""

from __future__ import annotations

from openai import OpenAI

from proactive_innovation.config import OPENROUTER_API_KEY, OPENROUTER_MODEL
from proactive_innovation.logging import log_info, log_warning


def call_llm(prompt: str, max_tokens: int = 1500) -> str:
    if not OPENROUTER_API_KEY:
        log_warning("llm:config", "No OPENROUTER_API_KEY")
        return "ERROR: No API key (OPENROUTER_API_KEY)"
    try:
        log_info("llm:try", "OpenRouter")
        client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
        resp = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:  # pylint: disable=broad-exception-caught
        log_warning("llm:error", f"OpenRouter: {str(e)[:80]}")
        return f"ERROR: {e}"
