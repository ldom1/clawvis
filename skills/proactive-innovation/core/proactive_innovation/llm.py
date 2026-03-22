"""LLM calls via MammouthAI (pay-per-token API). Used at most twice per run (improvements + ideas)."""

from __future__ import annotations

from openai import OpenAI

from proactive_innovation.config import MAMMOUTH_API_KEY
from proactive_innovation.logging import log_info, log_warning


def call_llm(prompt: str, max_tokens: int = 1500) -> str:
    """One call: MammouthAI. Requires MAMMOUTH_API_KEY (openclaw.json or .env)."""
    if not MAMMOUTH_API_KEY:
        log_warning("llm:config", "No MAMMOUTH_API_KEY")
        return "ERROR: No API key (MAMMOUTH_API_KEY)"
    try:
        log_info("llm:try", "MammouthAI")
        client = OpenAI(
            api_key=MAMMOUTH_API_KEY,
            base_url="https://api.mammouth.ai/v1",
        )
        resp = client.chat.completions.create(
            model="mistral-small-3.2-24b-instruct",
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return (resp.choices[0].message.content or "").strip()
    except Exception as e:  # pylint: disable=broad-exception-caught
        log_warning("llm:error", f"MammouthAI: {str(e)[:80]}")
        return f"ERROR: {e}"
