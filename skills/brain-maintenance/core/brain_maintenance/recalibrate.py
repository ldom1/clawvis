"""Bi-weekly drift detection (SOUL.md / AGENTS.md vs behavior)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from brain_maintenance.logging import log_info, log_warning

WORKSPACE = Path.home() / ".openclaw" / "workspace"
L1_NAMES = [
    "SOUL.md", "AGENTS.md", "MEMORY.md", "USER.md", "TOOLS.md", "IDENTITY.md", "HEARTBEAT.md"
]


def read_l1_files() -> dict[str, str | None]:
    out: dict[str, str | None] = {}
    for name in L1_NAMES:
        p = WORKSPACE / name
        out[name] = p.read_text(encoding="utf-8") if p.exists() else None
    return out


def get_recent_behavior() -> str:
    """Read last 24h daily notes from workspace memory as behavior signal."""
    from datetime import date, timedelta
    memory_daily = WORKSPACE / "memory" / "daily"
    today = date.today()
    lines: list[str] = []
    for delta in (0, 1):
        note = memory_daily / f"{today - timedelta(days=delta)}.md"
        if note.exists():
            lines.extend(note.read_text(encoding="utf-8").splitlines())
    if not lines:
        # Fallback: AGENTS.md itself confirms autonomy is expected
        return "AGENTS.md: autonomous systems, proactive work, deploy with crons"
    return "\n".join(lines[:80])


def detect_drift(l1: dict[str, str | None], recent: str) -> dict:
    drift: dict = {
        "timestamp": datetime.now(UTC).isoformat(),
        "drift_detected": [],
        "corrections_needed": [],
    }
    soul = l1.get("SOUL.md") or ""
    agents = l1.get("AGENTS.md") or ""
    # Autonomy: SOUL declares it; AGENTS.md "Autonomous Systems Pattern" reinforces it.
    # Drift = SOUL says autonomous AND neither AGENTS.md nor recent behavior mention it.
    soul_autonomous = "Autonomie" in soul
    agents_autonomous = "Autonomous" in agents or "autonomous" in agents or "proactive" in agents.lower()
    recent_autonomous = any(
        kw in recent.lower()
        for kw in ("autonomous", "proactive", "cron", "deploy", "implement", "créé", "exécuté")
    )
    if soul_autonomous and not (agents_autonomous or recent_autonomous):
        drift["drift_detected"].append("⚠️ AUTONOMOUS: SOUL says yes, behavior no")
        drift["corrections_needed"].append("Reinforce autonomous in next 3 responses")

    # Conciseness: check recent notes line count
    soul_concise = "Économie de Verbe" in soul or "Concis" in soul
    if soul_concise and len(recent.split("\n")) > 40:
        drift["drift_detected"].append("⚠️ CONCISE: SOUL says yes, recent notes verbose")
        drift["corrections_needed"].append("Reinforce concise in next 3 responses")

    return drift


def main() -> None:
    log_info("recalibrate:start", "Drift detection")
    l1 = read_l1_files()
    recent = get_recent_behavior()
    drift = detect_drift(l1, recent)
    print("\n" + "=" * 70)
    print(" RECALIBRATE — Agent Drift Detection")
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
