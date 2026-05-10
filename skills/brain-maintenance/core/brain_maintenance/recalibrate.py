"""Drift detection: CLAUDE.md / AGENTS.md vs recent memory notes."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from brain_maintenance.clawvis_paths import agent_workspace, brain_path, memory_root
from brain_maintenance.logging import log_info, log_warning

WORKSPACE = agent_workspace()
L1_NAMES = ["CLAUDE.md", "AGENTS.md", "README.md"]


def read_l1_files() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name in L1_NAMES:
        p = WORKSPACE / name
        out[name] = p.read_text(encoding="utf-8") if p.exists() else None
    return out


def get_recent_behavior() -> str:
    """Read last 24h notes as behavior signal.

    Primary: Local Brain vault (BRAIN_PATH/inbox/daily/implementation/clawvis/).
    Fallback: Clawvis instance memory (MEMORY_ROOT/daily/).
    """
    from datetime import date, timedelta

    today = date.today()
    lines: list[str] = []

    bp = brain_path()
    if bp:
        brain_daily = bp / "inbox" / "daily" / "implementation" / "clawvis"
        for delta in (0, 1):
            day = today - timedelta(days=delta)
            if brain_daily.exists():
                for note in sorted(brain_daily.glob(f"{day}-*.md"), reverse=True):
                    lines.extend(note.read_text(encoding="utf-8").splitlines())
        if lines:
            return "\n".join(lines[:80])

    memory_daily = memory_root() / "daily"
    for delta in (0, 1):
        note = memory_daily / f"{today - timedelta(days=delta)}.md"
        if note.exists():
            lines.extend(note.read_text(encoding="utf-8").splitlines())
    if lines:
        return "\n".join(lines[:80])

    return (
        "AGENTS.md: verify commands/tests; update docs when behavior changes; "
        "stack hub kanban-api hub-memory-api agent telegram scheduler"
    )


def detect_drift(l1: dict[str, str | None], recent: str) -> dict:
    drift: dict = {
        "timestamp": datetime.now(UTC).isoformat(),
        "drift_detected": [],
        "corrections_needed": [],
    }
    agents = (l1.get("AGENTS.md") or "").lower()
    claude = (l1.get("CLAUDE.md") or "").lower()
    recent_l = recent.lower()

    if "verify" in agents and not any(
        k in recent_l for k in ("verify", "test", "pytest", "ci-all", "tests/")
    ):
        drift["drift_detected"].append(
            "⚠️ VERIFY: AGENTS.md expects verification; recent notes lack test/verify signal"
        )
        drift["corrections_needed"].append("Run or note verification (tests/CI) for recent work")

    docs_cue = "documentation" in agents or "changelog" in claude
    if docs_cue and len(recent.split()) > 40 and not any(
        k in recent_l for k in ("doc", "changelog", "readme", "skill.md", "docs/")
    ):
        drift["drift_detected"].append(
            "⚠️ DOCS: CLAUDE/AGENTS stress doc updates; recent long notes omit doc/changelog cues"
        )
        drift["corrections_needed"].append("Mention docs/CHANGELOG when behavior or setup changed")

    return drift


def main() -> None:
    log_info("recalibrate:start", "Drift detection")
    l1 = read_l1_files()
    recent = get_recent_behavior()
    drift = detect_drift(l1, recent)
    print("\n" + "=" * 70)
    print(" RECALIBRATE — Agent drift vs CLAUDE.md / AGENTS.md")
    print("=" * 70 + "\n")
    if drift["drift_detected"]:
        for issue in drift["drift_detected"]:
            print(f"   {issue}")
        log_warning("recalibrate:drift", f"{len(drift['drift_detected'])} issues")
    else:
        print("✅ NO DRIFT DETECTED")
        log_info("recalibrate:ok", "Aligned")
    log_dir = WORKSPACE / ".logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"recalibrate-{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    log_file.write_text(
        json.dumps({
            "timestamp": drift["timestamp"],
            "drift_detected": len(drift["drift_detected"]) > 0,
            "issues": drift["drift_detected"],
            "corrections": drift["corrections_needed"],
        }, indent=2),
        encoding="utf-8",
    )
    log_info("recalibrate:complete", str(log_file))
    print(f"\n✅ Report saved: {log_file}\n")
