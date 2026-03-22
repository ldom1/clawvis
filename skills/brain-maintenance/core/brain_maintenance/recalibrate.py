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
    return """
[Recent behavior examples]
- Last message: Direct, concise, no fluff
- Tool usage: Chose read over web_search when local file available
- Error handling: Apologized briefly, proposed fix
"""


def detect_drift(l1: dict[str, str | None], recent: str) -> dict:
    drift: dict = {
        "timestamp": datetime.now(UTC).isoformat(),
        "drift_detected": [],
        "corrections_needed": [],
    }
    soul = l1.get("SOUL.md") or ""
    soul_traits = {
        "concise": "Économie de Verbe" in soul or "Concis" in soul,
        "autonomous": "Autonomie" in soul,
    }
    behavior_traits = {
        "concise": len(recent.split("\n")) < 20,
        "autonomous": "I'll implement" in recent or "I'll create" in recent,
    }
    for trait, soul_says in soul_traits.items():
        if soul_says and not behavior_traits.get(trait, False):
            drift["drift_detected"].append(f"⚠️ {trait.upper()}: SOUL says yes, behavior no")
            drift["corrections_needed"].append(f"Reinforce {trait} in next 3 responses")
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
