"""Report sending: Slack only (no Telegram messages)."""

from __future__ import annotations

import sys

from self_improvment.logging import log_info


def send_report(text: str) -> None:
    """Log report (important output only). No Telegram messages.
    Slack will be notified by dombot-logger via cron process."""
    # Report is logged locally + added to MEMORY.md
    # Process start/end logged to dombot-logger + Slack
    # No Telegram messages (only important discoveries sent separately)
    log_info("self-improvement:report", text[:500])
    print("✅ Report logged (Slack via logger)", file=sys.stderr)
