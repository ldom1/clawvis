"""Entry point for python -m self_improvment."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime

from self_improvment.config import LEARNINGS_DIR, OPENROUTER_API_KEY, WORKSPACE
from self_improvment.learnings import analyze_learnings
from self_improvment.logging import log_error, log_info
from self_improvment.protocol_audit import run_protocol_audit
from self_improvment.telegram import send_report


def main() -> None:
    os.chdir(WORKSPACE)

    mode = sys.argv[1] if len(sys.argv) > 1 else "review"

    if mode == "protocol_audit":
        print("🔎 Running protocol_audit mode…")
        log_info("cron:start", "protocol_audit started")
        status = run_protocol_audit()
        log_info("cron:complete", f"protocol_audit finished: {status}", status=status)
        print(f"Summary status: {status}")
        return

    print("🔍 Self-Improvement Review started...")
    log_info("cron:start", "Self-Improvement Review started")
    if OPENROUTER_API_KEY:
        print("   LLM: OpenRouter ✅")
    else:
        print("   LLM: ❌ (set OPENROUTER_API_KEY in Clawvis `.env`)")

    LEARNINGS_DIR.mkdir(exist_ok=True)
    print("📊 Analyzing learnings...")
    analysis = analyze_learnings()

    if analysis.startswith("ERROR"):
        log_error("cron:fail", analysis[:500], status="error")
        print(f"❌ {analysis}")
        sys.exit(1)

    print(f"✨ Analysis:\n{analysis}")
    # Note: Analysis is logged via send_report() and dombot-logger
    # NOT written to MEMORY.md (reserved for manual updates only)

    log_file = LEARNINGS_DIR / "review.json"
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "analysis": analysis[:500],
        "status": "success",
    }

    logs: list[dict] = []
    if log_file.exists():
        with open(log_file, encoding="utf-8") as f:
            logs = json.load(f)
    logs.append(log_entry)

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(logs[-10:], f, indent=2)

    log_info("cron:complete", "Self-Improvement Review complete", status="success")
    print("✅ Self-improvement review complete")

    send_report(analysis[:500])


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log_error("cron:fail", str(e)[:500], status="error")
        raise
