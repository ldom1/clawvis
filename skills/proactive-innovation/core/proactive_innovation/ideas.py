"""Phase 3: one LLM call for ideas, append to entrepreneur.md (bounded)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from proactive_innovation.config import (
    CURIOSITY_DIR,
    ENTREPRENEUR_FILE,
    IDEA_SECTION_HEADER,
    KNOWLEDGE_DIR,
    MAX_IDEAS_PER_RUN,
)
from proactive_innovation.llm import call_llm
from proactive_innovation.logging import log_warning


def _sample_paths() -> list[Path]:
    out: list[Path] = []
    for d in (KNOWLEDGE_DIR, CURIOSITY_DIR):
        if d.exists():
            for f in sorted(d.rglob("*.md"))[:5]:
                out.append(f)
                if len(out) >= 10:
                    return out
    return out


def _read_safe(path: Path, limit: int = 500) -> str:
    try:
        return path.read_text(encoding="utf-8")[:limit]
    except OSError:
        return ""


def run_phase3() -> tuple[int, list[str]]:
    """Suggest up to MAX_IDEAS_PER_RUN ideas, append to entrepreneur. Returns (count, report_lines)."""
    if not ENTREPRENEUR_FILE.exists():
        return 0, ["Caps entrepreneur introuvable."]

    paths = _sample_paths()
    context = "\n---\n".join(_read_safe(p) for p in paths) or "Aucune ressource."
    prompt = (
        f"Tu es DomBot. À partir des extraits ci-dessous, propose {MAX_IDEAS_PER_RUN} idée(s) "
        "entreprise/OSS/side-project (une phrase ou un court paragraphe par idée).\n"
        "Réponds UNIQUEMENT par des lignes numérotées (1. idée... 2. idée...). Pas d'intro.\n\n"
        + context
    )
    response = call_llm(prompt, max_tokens=600)
    if response.startswith("ERROR"):
        log_warning("phase3:llm", response[:200])
        return 0, [f"Phase 3 LLM: {response[:200]}."]

    ideas: list[str] = []
    for line in response.strip().splitlines():
        line = line.strip()
        if not line:
            continue
        if line[0].isdigit() and (". " in line or ".) " in line):
            _, _, rest = line.partition(". ") if ". " in line else line.partition(".) ")
            ideas.append(rest.strip())
        else:
            ideas.append(line)
        if len(ideas) >= MAX_IDEAS_PER_RUN:
            break

    if not ideas:
        return 0, ["0 idée ajoutée."]

    try:
        content = ENTREPRENEUR_FILE.read_text(encoding="utf-8")
    except OSError:
        return 0, ["Erreur lecture entrepreneur."]
    today = datetime.now().strftime("%Y-%m-%d")
    block = "\n\n".join(f"### [{today}] {t}" for t in ideas)
    if IDEA_SECTION_HEADER not in content:
        content += "\n\n" + IDEA_SECTION_HEADER + "\n\n" + block + "\n"
    else:
        start = content.find(IDEA_SECTION_HEADER)
        end = content.find("\n## ", start + len(IDEA_SECTION_HEADER))
        if end == -1:
            end = len(content)
        insert = content[start:end].rstrip() + "\n\n" + block + "\n"
        content = content[:start] + insert + content[end:]

    try:
        ENTREPRENEUR_FILE.write_text(content, encoding="utf-8")
    except OSError:
        return 0, ["Erreur écriture entrepreneur."]

    return len(ideas), [f"{len(ideas)} idée(s) → entrepreneur."]
