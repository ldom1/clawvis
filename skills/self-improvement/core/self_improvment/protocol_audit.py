"""Protocol audit: scan skills and Lab projects."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from self_improvment.config import CLAWVIS_ROOT_PATH, LAB_ROOT, LAB_ROOT_LEGACY
from self_improvment.logging import log_info


def _read_text(path: Path, limit: int | None = None) -> str:
    try:
        txt = path.read_text(encoding="utf-8")
        return txt if limit is None else txt[:limit]
    except OSError:
        return ""


def _check_pyproject(pyproject: Path) -> dict:
    data: dict = {"path": str(pyproject), "status": "OK", "notes": []}
    try:
        raw = pyproject.read_text(encoding="utf-8")
    except OSError as e:
        data["status"] = "WARN"
        data["notes"].append(f"Impossible de lire pyproject.toml: {e}")
        return data
    if "uv" not in raw:
        data["status"] = "WARN"
        data["notes"].append("Pas de mention explicite de uv dans pyproject.toml")
    if "pydantic" not in raw:
        data["notes"].append("pydantic non détecté (peut être OK si non nécessaire)")
    return data


def _scan_lab_projects() -> list[dict]:
    results: list[dict] = []
    for lab in (LAB_ROOT, LAB_ROOT_LEGACY):
        if not lab.is_dir():
            continue
        for root in (lab / "poc", lab / "project"):
            if not root.exists():
                continue
            for project in root.iterdir():
                if not project.is_dir():
                    continue
                pyproject = project / "pyproject.toml"
                if not pyproject.exists():
                    results.append(
                        {
                            "project": str(project),
                            "status": "WARN",
                            "notes": ["Aucun pyproject.toml détecté"],
                        }
                    )
                    continue
                info = _check_pyproject(pyproject)
                env_example = project / ".env.example"
                if not env_example.exists():
                    info["notes"].append(".env.example manquant")
                    if info["status"] == "OK":
                        info["status"] = "WARN"
                info["project"] = str(project)
                results.append(info)
    return results


def _scan_skills() -> list[dict]:
    roots: list[Path] = []
    if CLAWVIS_ROOT_PATH is not None:
        s = CLAWVIS_ROOT_PATH / "skills"
        if s.is_dir():
            roots.append(s)

    results: list[dict] = []
    for root in roots:
        for skill in root.iterdir():
            if not skill.is_dir():
                continue
            skill_md = skill / "SKILL.md"
            if not skill_md.exists():
                continue
            txt = _read_text(skill_md, limit=2000)
            status = "OK"
            notes: list[str] = []
            if "uv run" not in txt and "pyproject.toml" in txt:
                notes.append("Mention pyproject.toml sans exemple uv run")
                status = "WARN"
            results.append({"skill": skill.name, "status": status, "notes": notes})
    return results


def _worst_status(items: list[dict]) -> str:
    level = "OK"
    for it in items:
        s = it.get("status", "OK")
        if s == "FIXME":
            return "FIXME"
        if s == "WARN" and level == "OK":
            level = "WARN"
    return level


def _first_protocol_text() -> tuple[str, str]:
    """Return (label, excerpt) from first PROTOCOL.md found under ~/lab or ~/Lab."""
    for lab in (LAB_ROOT, LAB_ROOT_LEGACY):
        p = lab / "PROTOCOL.md"
        if p.is_file():
            return str(p), _read_text(p, limit=4000)
    return "", ""


def run_protocol_audit() -> str:  # pylint: disable=too-many-statements
    """Run protocol audit and write report to /tmp/protocol-audit-report.md."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    report_path = Path("/tmp/protocol-audit-report.md")

    proto_label, proto = _first_protocol_text()
    skills = _scan_skills()
    projects = _scan_lab_projects()

    status_skills = _worst_status(skills)
    status_projects = _worst_status(projects)
    overall = "OK"
    if "FIXME" in (status_skills, status_projects):
        overall = "FIXME"
    elif "WARN" in (status_skills, status_projects):
        overall = "WARN"

    lines: list[str] = []
    lines.append(f"# Protocol Audit — {ts}")
    lines.append("")
    lines.append(f"**Statut global**: {overall}")
    lines.append("")
    lines.append("## Résumé")
    lines.append(f"- Skills: {status_skills}")
    lines.append(f"- Projets Python (poc/project): {status_projects}")
    lines.append("")
    lines.append("## PROTOCOL.md (extrait)")
    if proto:
        lines.append(f"_Source : `{proto_label}`_")
        lines.append("")
        lines.append("```markdown")
        lines.append(proto)
        lines.append("```")
    else:
        lines.append("")
        lines.append("_PROTOCOL.md introuvable sous ~/lab ou ~/Lab_")

    lines.append("")
    lines.append("## Skills")
    if not skills:
        scan_hint = (
            f"`{CLAWVIS_ROOT_PATH / 'skills'}`"
            if CLAWVIS_ROOT_PATH is not None
            else "~/lab/clawvis/skills (définir CLAWVIS_ROOT ou checkout repo)"
        )
        lines.append(f"- Aucun skill détecté sous {scan_hint}.")
    else:
        for s in skills:
            notes = "; ".join(s.get("notes") or []) or "RAS"
            lines.append(f"- **{s['skill']}** — {s['status']} · {notes}")

    lines.append("")
    lines.append("## Projets Python (poc/project)")
    if not projects:
        lines.append("- Aucun projet détecté sous `~/lab/{poc,project}` ou `~/Lab/{poc,project}`.")
    else:
        for p in projects:
            notes = "; ".join(p.get("notes") or []) or "RAS"
            lines.append(f"- **{p['project']}** — {p['status']} · {notes}")

    text = "\n".join(lines)
    report_path.write_text(text, encoding="utf-8")
    log_info("protocol_audit:report", str(report_path))
    print(f"✅ Protocol audit report written to {report_path}")
    return overall
