"""Normalize scheduler → Telegram payloads (plain text; no parse_mode)."""

from __future__ import annotations

import re

_MULTI_BLANK = re.compile(r"\n{3,}")
_BOLD = re.compile(r"\*\*([^*]+)\*\*")
_UNDER = re.compile(r"__(?!_)([^_]+)__(?!_)")


def format_job_telegram_body(text: str) -> str:
    """Strip Markdown markers that render literally in Telegram; tighten whitespace."""
    t = text.strip()
    if not t:
        return t
    t = _BOLD.sub(r"\1", t)
    t = _UNDER.sub(r"\1", t)
    t = _MULTI_BLANK.sub("\n\n", t)
    return "\n".join(line.rstrip() for line in t.splitlines())
