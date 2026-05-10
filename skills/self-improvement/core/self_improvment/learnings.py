"""Learnings analysis and memory update."""

from __future__ import annotations

from self_improvment.config import LEARNINGS_DIR
from self_improvment.llm import call_llm


def analyze_learnings() -> str:
    """Analyze .learnings directory and generate recommendations."""
    learnings_file = LEARNINGS_DIR / "LEARNINGS.md"
    errors_file = LEARNINGS_DIR / "ERRORS.md"
    todos_file = LEARNINGS_DIR / "TODO.md"

    context = "Current state:\n"
    if learnings_file.exists():
        context += f"\n=== LEARNINGS ({learnings_file.stat().st_size} bytes) ===\n"
        context += learnings_file.read_text(encoding="utf-8")[:500] + "..."

    if errors_file.exists():
        context += "\n\n=== ERRORS ===\n"
        context += errors_file.read_text(encoding="utf-8")[:300] + "..."

    if todos_file.exists():
        context += "\n\n=== TODOS ===\n"
        context += todos_file.read_text(encoding="utf-8")[:500] + "..."

    prompt = f"""You are DomBot's Self-Improvement Agent. Analyze the current state and provide SPECIFIC, DETAILED recommendations.

{context}

Generate a structured report with CONCRETE action items. NO PLACEHOLDERS, NO "(Details in log)". ACTUAL VALUES ONLY.

**What's Working (Keep Doing It)**
- List 2-3 specific things working well with metrics or details
- Examples: "100% uptime for X", "Reduced Y by Z%", "Successfully automated W"

**What Needs Fixing (Priority Order)**
- List 2-3 specific issues, ranked by priority
- Each item: short title + 1-line reason/context
- Examples: "Fix OpenRouter rate limits on batch ingest", "Resolve hub-memory-api timeouts"

**Innovation To Try**
- ONE specific, actionable idea to test in next 24h
- Examples: "Implement sliding window for discovery retention", "Parallelize agent workflows"

CRITICAL: Be 100% specific. Every bullet point must be concrete and actionable. No "(Details in log)" placeholders. Max 300 tokens."""

    return call_llm(prompt)
