"""Phase 1: scan projects, ensure section, append improvements (single LLM call for all)."""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

from proactive_innovation.config import (
    MAX_IMPROVEMENTS_PER_PROJECT,
    MAX_PROJECTS_PER_RUN,
    PROJECTS_DIR,
    SECTION_HEADER,
    TIMELINE_HEADER,
)
from proactive_innovation.llm import call_llm
from proactive_innovation.logging import log_warning


def _list_projects() -> list[Path]:
    if not PROJECTS_DIR.exists():
        return []
    out: list[Path] = []
    for p in sorted(PROJECTS_DIR.glob("*.md")):
        if p.name.startswith("_") or p.name.lower() == "readme.md":
            continue
        out.append(p)
        if len(out) >= MAX_PROJECTS_PER_RUN:
            break
    return out


def _read_md(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def _extract_section(content: str, header: str) -> str | None:
    m = re.search(rf"^({re.escape(header)})\s*$", content, re.MULTILINE)
    if not m:
        return None
    start = m.end()
    next_hr = content.find("\n## ", start)
    if next_hr == -1:
        return content[start:].strip()
    return content[start:next_hr].strip()


def _existing_improvements(content: str) -> set[str]:
    section = _extract_section(content, SECTION_HEADER)
    if not section:
        return set()
    lines = [ln.strip() for ln in section.splitlines() if ln.strip() and ln.strip().startswith("-")]
    return set(lines)


def _ensure_section(content: str) -> str:
    if SECTION_HEADER in content:
        return content
    # Insert after Timeline and before ## Ressources or ## Notes
    insert_m = re.search(rf"^({re.escape(TIMELINE_HEADER)})\s*$", content, re.MULTILINE)
    if insert_m:
        # Find end of Timeline block (next ## or end)
        after = content[insert_m.end():]
        next_sec = re.search(r"\n## ", after)
        pos = insert_m.end() + (next_sec.start() if next_sec else len(after))
        new_block = "\n\n" + SECTION_HEADER + "\n\n_Propositions auto (format: - **YYYY-MM-DD** — Description)._\n\n"
        return content[:pos] + new_block + content[pos:]
    return content + "\n\n" + SECTION_HEADER + "\n\n"


def _parse_llm_improvements(text: str) -> list[tuple[str, str]]:
    """Parse lines like 'project_name|improvement' or 'project_name — improvement'."""
    out: list[tuple[str, str]] = []
    for line in text.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" in line:
            a, _, b = line.partition("|")
            out.append((a.strip(), b.strip()))
        elif "—" in line or " - " in line:
            sep = "—" if "—" in line else " - "
            a, _, b = line.partition(sep)
            out.append((a.strip(), b.strip()))
        if len(out) >= MAX_PROJECTS_PER_RUN * MAX_IMPROVEMENTS_PER_PROJECT:
            break
    return out


def run_phase1() -> tuple[int, int, list[str]]:
    """
    Scan projects, one LLM call for suggestions, append to section. Never send messages.
    Returns (projects_scanned, improvements_added, report_lines).
    """
    projects = _list_projects()
    if not projects:
        return 0, 0, ["Aucun projet dans memory/projects."]

    summaries: list[str] = []
    path_by_name: dict[str, Path] = {}
    for p in projects:
        name = p.stem
        path_by_name[name] = p
        raw = _read_md(p)
        if not raw:
            continue
        obj = _extract_section(raw, "## Objectif") or ""
        timeline = _extract_section(raw, TIMELINE_HEADER) or ""
        summaries.append(f"Projet: {name}\nObjectif: {obj[:300]}\nTimeline: {timeline[:200]}")

    prompt = (
        "Tu es DomBot. Pour chaque projet ci-dessous, propose 1 à "
        + str(MAX_IMPROVEMENTS_PER_PROJECT)
        + " améliorations courtes (fix, perf, DX, sécurité).\n"
        "Réponds UNIQUEMENT par des lignes au format: nom_projet|description courte (pas de puce).\n"
        "Pas d'intro ni conclusion.\n\n"
        + "\n---\n".join(summaries)
    )
    response = call_llm(prompt, max_tokens=800)
    if response.startswith("ERROR"):
        log_warning("phase1:llm", response[:200])
        return len(projects), 0, [f"Phase 1 LLM: {response[:200]}."]

    today = datetime.now().strftime("%Y-%m-%d")
    parsed = _parse_llm_improvements(response)
    by_project: dict[Path, list[str]] = {}
    for proj_name, improvement in parsed:
        if improvement in ("", "—", "-"):
            continue
        path = path_by_name.get(proj_name) or path_by_name.get(proj_name.replace(" ", "-").lower())
        if not path:
            continue
        content = _read_md(path)
        existing = _existing_improvements(content)
        new_line = f"- **{today}** — {improvement}"
        if new_line in existing:
            continue
        by_project.setdefault(path, []).append(new_line)

    added = 0
    for path, new_lines in by_project.items():
        content = _read_md(path)
        content = _ensure_section(content)
        existing_lines = _extract_section(content, SECTION_HEADER) or ""
        if existing_lines and not existing_lines.endswith("\n"):
            existing_lines += "\n"
        new_section_body = existing_lines + "\n".join(new_lines) + "\n"
        start = content.find(SECTION_HEADER)
        if start == -1:
            continue
        end_sec = content.find("\n## ", start + len(SECTION_HEADER))
        if end_sec == -1:
            end_sec = len(content)
        new_content = content[:start] + SECTION_HEADER + "\n\n" + new_section_body.strip() + "\n\n" + content[end_sec:]
        try:
            path.write_text(new_content, encoding="utf-8")
            added += len(new_lines)
        except OSError:
            pass

    report = [f"{len(projects)} projet(s) scanné(s), {added} amélioration(s) ajoutée(s)."]
    return len(projects), added, report
