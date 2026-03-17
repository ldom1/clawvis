"""Session token tracker — fetches real usage from openclaw status + MammouthAI API."""

import json
import subprocess
from datetime import datetime
from pathlib import Path

from loguru import logger

from hub_core.config import LAB_DIR
from hub_core.fetch.mammouth_ai_usage import get_mammouth_credits


def get_openclaw_status() -> dict | None:
    """Fetch Claude session usage from openclaw status --json."""
    try:
        result = subprocess.run(
            ["openclaw", "status", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            logger.warning(f"openclaw status failed: {result.stderr}")
            return None

        data = json.loads(result.stdout)
        claude = data.get("claude", {})
        return {
            "usage_percent": claude.get("usage_percent", 0),
            "tokens_used": claude.get("tokens_used", "0"),
            "tokens_limit": claude.get("tokens_limit", "0"),
            "reset_time": claude.get("reset_time", "unknown"),
            "session_count": len(data.get("sessions", [])),
        }
    except Exception as e:
        logger.error(f"Error getting openclaw status: {e}")
        return None


def update_session_tokens() -> dict:
    """Update token tracking JSON with latest Claude + MammouthAI data.

    Writes to: ~/Lab/hub/public/api/session-tokens.json
    Returns the written data dict.
    """
    output_file = LAB_DIR / "hub" / "public" / "api" / "session-tokens.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    claude = get_openclaw_status() or {
        "usage_percent": 0,
        "tokens_used": "0",
        "tokens_limit": "0",
        "reset_time": "unknown",
        "error": "OpenClaw status unavailable",
    }
    logger.info(f"Claude: {claude.get('usage_percent', 0)}% usage")

    mammouth_usage = get_mammouth_credits()
    if mammouth_usage:
        mammouth_data = {
            "subscription": mammouth_usage.subscription,
            "credits": {
                "available": mammouth_usage.credits.available,
                "limit": mammouth_usage.credits.limit,
                "currency": mammouth_usage.credits.currency,
            },
            "last_updated": mammouth_usage.last_updated,
        }
        logger.info(f"MammouthAI: {mammouth_usage.subscription}")
    else:
        mammouth_data = {"status": "not_configured", "note": "Set MAMMOUTH_API_KEY in .env"}

    session_data = {
        "updated_at": datetime.now().isoformat(),
        "claude": claude,
        "mammouth": mammouth_data,
    }
    output_file.write_text(json.dumps(session_data, indent=2))
    logger.info(f"Session tokens updated: {output_file}")
    return session_data


if __name__ == "__main__":
    print(json.dumps(update_session_tokens(), indent=2))
