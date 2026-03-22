"""Weekly L1 file audit (token budget)."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

from brain_maintenance.logging import log_info, log_warning

WORKSPACE = Path.home() / ".openclaw" / "workspace"
L1_FILES = {
    "SOUL.md": 1500,
    "AGENTS.md": 3500,  # behavioral rules — intentionally large
    "MEMORY.md": 1800,
    "USER.md": 500,
    "TOOLS.md": 900,
    "IDENTITY.md": 300,
    "HEARTBEAT.md": 300,
}
L1_TOTAL_BUDGET = 8800


def count_tokens(text: str) -> int:
    return len(text) // 4


def audit_l1_files() -> dict:
    report: dict = {
        "timestamp": datetime.now(UTC).isoformat(),
        "files": {},
        "total_tokens": 0,
        "budget_status": "OK",
        "recommendations": [],
    }
    for filename, budget in L1_FILES.items():
        filepath = WORKSPACE / filename
        if not filepath.exists():
            report["files"][filename] = {"status": "missing", "tokens": 0, "budget": budget}
            continue
        content = filepath.read_text(encoding="utf-8")
        tokens = count_tokens(content)
        ratio = tokens / budget
        status = "BLOATED" if ratio > 1.5 else ("OVER" if ratio >= 1.0 else "OK")
        report["files"][filename] = {
            "status": status,
            "tokens": tokens,
            "budget": budget,
            "ratio": round(ratio, 2),
        }
        report["total_tokens"] += tokens
        if status == "BLOATED":
            report["recommendations"].append(
                f"🔴 {filename}: {tokens} tokens (budget {budget}). "
                "Archive to memory/ or reference/."
            )
        elif status == "OVER":
            report["recommendations"].append(
                f"🟡 {filename}: {tokens} tokens (budget {budget}). Monitor."
            )
    if report["total_tokens"] > L1_TOTAL_BUDGET:
        report["budget_status"] = "OVER"
        report["recommendations"].insert(
            0,
            f"🔴 Total L1: {report['total_tokens']} tokens (budget {L1_TOTAL_BUDGET}). Trim now.",
        )
    return report


def print_report(report: dict) -> None:
    print("\n" + "=" * 70)
    print(" TRIM AUDIT — L1 Brain File Maintenance")
    print("=" * 70 + "\n")
    print("📊 L1 File Sizes:")
    for filename in L1_FILES:
        info = report["files"][filename]
        if info["status"] == "missing":
            print(f"   {filename:20} [MISSING]")
        else:
            ratio_pct = int(info["ratio"] * 100)
            icon = {"OK": "✅", "OVER": "🟡", "BLOATED": "🔴"}[info["status"]]
            print(
                f"   {filename:20} {info['tokens']:4} / {info['budget']:4} "
                f"tokens {ratio_pct:3}% {icon}"
            )
    total_pct = int((report["total_tokens"] / L1_TOTAL_BUDGET) * 100)
    icon = "✅" if report["budget_status"] == "OK" else "🔴"
    print(
        f"\n   {'Total L1':20} {report['total_tokens']:4} / {L1_TOTAL_BUDGET:4} "
        f"tokens {total_pct:3}% {icon}"
    )
    if report["recommendations"]:
        print("\n🎯 Recommendations:")
        for rec in report["recommendations"]:
            print(f"   {rec}")
    else:
        print("\n✅ All files within budget.")
    print("\n" + "=" * 70 + "\n")


def main() -> int:
    log_info("trim:start", "L1 trim audit")
    report = audit_l1_files()
    print_report(report)
    log_dir = WORKSPACE / ".logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"trim-audit-{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.json"
    log_file.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if report["budget_status"] != "OK":
        log_warning("trim:over", f"Total {report['total_tokens']} tokens")
    log_info("trim:complete", f"Audit saved: {log_file.name}")
    print(f"✅ Audit saved: {log_file.name}\n")
    return 0 if report["budget_status"] == "OK" else 1
