# agent/agent_service/persona.py
from __future__ import annotations

from pathlib import Path

_FALLBACK = (
    "You are the Clawvis assistant — the control tower for your AI agent infrastructure. "
    "You help the user manage projects, tasks, and knowledge in a structured, traceable way. "
    "Be concise, direct, and actionable."
)


def load_persona(state_dir: str | None) -> str:
    if not state_dir:
        return _FALLBACK

    workspace = Path(state_dir) / "workspace"
    parts: list[str] = []

    for fname in ("IDENTITY.md", "SOUL.md"):
        path = workspace / fname
        if path.exists():
            content = path.read_text(encoding="utf-8").strip()
            if content:
                parts.append(content)

    return "\n\n---\n\n".join(parts) if parts else _FALLBACK
