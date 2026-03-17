#!/usr/bin/env python3
"""Unified token stats — Claude (via openclaw status) + MammouthAI credits."""

import json
from hub_core.config import TOKENS_JSON
from hub_core.track.session import update_session_tokens
from loguru import logger


def get_token_stats():
    """Return unified token stats from openclaw + MammouthAI."""
    data = update_session_tokens()

    claude = data.get("claude", {})
    mammouth = data.get("mammouth", {})

    return {
        "claude": claude,
        "mammouth": mammouth,
        "timestamp": data.get("updated_at"),
    }


def main():
    stats = get_token_stats()
    TOKENS_JSON.parent.mkdir(parents=True, exist_ok=True)
    TOKENS_JSON.write_text(json.dumps(stats, indent=2))
    logger.info("✅ Token stats updated: {}", TOKENS_JSON)
    return 0


if __name__ == "__main__":
    exit(main())
