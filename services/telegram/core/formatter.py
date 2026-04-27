from __future__ import annotations

_MAX_LEN = 4096

_ERROR_SENTINELS = (
    "[Error:",
    "[CLI error:",
    "[CLI timeout:",
    "[CLI:",
    "[No LLM",
    "[CLAWVIS:",
)

_SNAG_MSG = (
    "I ran into a snag with that — try rephrasing or use /status to check the agent."
)
_EMPTY_MSG = (
    "Got an empty response. Try /status to verify the agent is configured."
)


def format_reply(raw: str) -> str:
    text = raw.strip()
    if not text:
        return _EMPTY_MSG
    # Pass through agent planning diagnostics (orchestration) so users see real errors.
    if text.startswith("[CLAWVIS:HTTP:") or text.startswith("[CLAWVIS:empty-content:"):
        return text[:_MAX_LEN]
    for sentinel in _ERROR_SENTINELS:
        if text.startswith(sentinel):
            return _SNAG_MSG
    return text[:_MAX_LEN]
