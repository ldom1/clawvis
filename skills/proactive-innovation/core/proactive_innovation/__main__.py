"""Entry point: run phases, print ONE report to stdout. No Telegram/OpenClaw calls."""

from __future__ import annotations

import os
import sys

from proactive_innovation.config import WORKSPACE
from proactive_innovation.ideas import run_phase3
from proactive_innovation.logging import log_error, log_info
from proactive_innovation.projects import run_phase1


def main() -> None:
    os.chdir(WORKSPACE)
    log_info("cron:start", "proactive-innovation run")
    report_lines: list[str] = []

    n_proj, n_imp, p1_report = run_phase1()
    report_lines.extend(p1_report)

    n_ideas, p3_report = run_phase3()
    report_lines.extend(p3_report)

    summary = " ".join(report_lines)
    if len(summary) > 280:
        summary = summary[:277] + "..."
    if report_lines:
        log_info("cron:complete", summary[:500], projects=n_proj, improvements=n_imp, ideas=n_ideas)
    if "ERROR" in summary:
        log_error("cron:fail", summary[:500])
    print(summary)
    if "ERROR" in summary:
        sys.exit(1)


if __name__ == "__main__":
    main()
