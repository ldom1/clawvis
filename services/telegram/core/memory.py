"""Telegram session memory — loads brain files at startup, saves summaries on shutdown."""
from __future__ import annotations

import re
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path

from loguru import logger as log

_LOAD_ORDER = [
    "clawvis-profile-ldom.md",
    "clawvis-memory.md",
    "clawvis-topics.md",
]
_SESSION_LOG = "clawvis-session-log.md"
_MEMORY_FILE = "clawvis-memory.md"
_TOPICS_FILE = "clawvis-topics.md"

_EXTRACTION_PROMPT = """\
You are a memory extractor for a Telegram assistant. Summarize the conversation below \
into three compact sections. Be extremely concise — each section has a hard cap.

## Active Context
(max 5 bullet points — key facts, decisions, or actions from this session)

## Pending Topics
(max 3 rows — unresolved threads; use pipe-separated format: Topic | Status | Date | Priority)

## Session Summary
(1 sentence max)

Conversation:
{conversation}

Output ONLY the three sections above. No preamble."""


class TelegramMemory:
    """Lightweight per-process memory injected into every agent prompt."""

    def __init__(self, brain_path: str | None) -> None:
        self._dir: Path | None = None
        self._prefix: str = ""
        self._exchanges: list[tuple[str, str]] = []  # (role, text)

        if brain_path:
            candidate = Path(brain_path) / "resources" / "knowledge" / "operational" / "clawvis"
            if candidate.exists():
                self._dir = candidate
                log.info("memory.dir=%s", self._dir)
            else:
                log.warning("memory.dir_missing path=%s — memory disabled", candidate)

    @property
    def enabled(self) -> bool:
        return self._dir is not None

    # ── Startup ───────────────────────────────────────────────────────────────

    def load(self) -> None:
        """Read brain files and build the context prefix injected into prompts."""
        if not self.enabled:
            return
        parts: list[str] = []
        for filename in _LOAD_ORDER:
            path = self._dir / filename  # type: ignore[operator]
            if path.exists():
                text = path.read_text(encoding="utf-8").strip()
                if text:
                    parts.append(text)

        if parts:
            self._prefix = (
                "=== Clawvis Memory Context ===\n"
                + "\n\n".join(parts)
                + "\n=== End Memory Context ===\n\n"
            )
            log.info("memory.loaded files=%d prefix_chars=%d", len(parts), len(self._prefix))
        else:
            log.info("memory.loaded_empty")

    # ── Per-message ───────────────────────────────────────────────────────────

    def inject(self, prompt: str) -> str:
        """Prepend the memory context block to the user prompt."""
        if not self._prefix:
            return prompt
        return self._prefix + prompt

    def record(self, role: str, text: str) -> None:
        """Track conversation for session-end extraction (keep last 30 turns)."""
        self._exchanges.append((role, text))
        if len(self._exchanges) > 30:
            self._exchanges = self._exchanges[-30:]

    # ── Shutdown ──────────────────────────────────────────────────────────────

    async def save(self, call_agent: Callable[[str], Awaitable[str]]) -> None:
        """Extract key points from the session and persist them to brain files."""
        if not self.enabled or not self._exchanges:
            log.info("memory.save_skipped enabled=%s exchanges=%d", self.enabled, len(self._exchanges))
            return

        conv_text = "\n".join(f"[{role}]: {text}" for role, text in self._exchanges)
        prompt = _EXTRACTION_PROMPT.format(conversation=conv_text)

        try:
            extracted = await call_agent(prompt)
            self._persist(extracted)
            log.info("memory.saved extracted_chars=%d", len(extracted))
        except Exception:
            log.exception("memory.save_error")

    def _persist(self, extracted: str) -> None:
        assert self._dir is not None
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        active = _section(extracted, "Active Context")
        pending = _section(extracted, "Pending Topics")
        summary = _section(extracted, "Session Summary")

        # clawvis-session-log.md — overwrite every session
        (_dir_path := self._dir / _SESSION_LOG).write_text(
            f"# Last Session Summary\n_Overwritten each session — not cumulative_\n\n"
            f"Date: {now}\n\n"
            f"## Key Exchanges\n{active or '_None._'}\n\n"
            f"## Session Summary\n{summary or '_N/A_'}\n",
            encoding="utf-8",
        )

        # clawvis-memory.md — replace Active Context and Pending Topics
        mem = self._dir / _MEMORY_FILE
        mem.write_text(
            f"# Clawvis Short-Term Memory\n_Last updated: {now}_\n\n"
            f"## Active Context (last session)\n{active or '_None._'}\n\n"
            f"## Pending Topics\n{pending or '_None._'}\n",
            encoding="utf-8",
        )

        # clawvis-topics.md — append new pending rows (deduplicated by first cell)
        if pending:
            _merge_topics(self._dir / _TOPICS_FILE, pending, now)


def _section(text: str, name: str) -> str:
    """Extract a named ## section from markdown text."""
    match = re.search(rf"## {re.escape(name)}\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    return match.group(1).strip() if match else ""


def _merge_topics(path: Path, pending_block: str, now: str) -> None:
    """Merge new topic rows into clawvis-topics.md, deduplicating by topic name."""
    existing_text = path.read_text(encoding="utf-8") if path.exists() else ""
    existing_rows: dict[str, str] = {}
    for line in existing_text.splitlines():
        if line.startswith("|") and "|" in line[1:]:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and cells[0] not in ("Topic", "---", ""):
                existing_rows[cells[0]] = line

    for line in pending_block.splitlines():
        line = line.strip()
        if "|" in line:
            cells = [c.strip() for c in line.strip("|").split("|")]
            if cells and cells[0] not in ("Topic", "---", ""):
                existing_rows[cells[0]] = f"| {' | '.join(cells)} |"

    header = "# Open Topics\n_Cleared when resolved_\n\n| Topic | Status | Last Mentioned | Priority |\n|-------|--------|----------------|----------|\n"
    rows = "\n".join(existing_rows.values())
    path.write_text(header + rows + "\n", encoding="utf-8")
