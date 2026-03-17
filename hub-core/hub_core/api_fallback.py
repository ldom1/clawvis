"""API fallback strategy: Claude → MammouthAI on rate limit or usage threshold.

Fallback triggers:
  1. Claude usage > 75% of daily quota (via openclaw status)
  2. Rate limit error message detected

Usage:
    should_fallback, reason = should_fallback_to_mammouth()
    if should_fallback:
        result = try_mammouth_request(prompt)
"""

import json
import os
import subprocess
from functools import wraps
from typing import Any, Callable, Dict, Optional

from loguru import logger


def is_rate_limit_error(error_message: str) -> bool:
    """Return True if the error indicates API rate limiting."""
    phrases = ["rate limit", "quota exceeded", "too many requests", "429", "throttle", "api limit"]
    return any(phrase in error_message.lower() for phrase in phrases)


# Keep old name as alias for backwards compatibility
is_rate_limited = is_rate_limit_error


def get_claude_usage_percent() -> Optional[float]:
    """Read Claude usage percentage from openclaw status.

    Returns percentage 0-100, or None on failure.
    """
    try:
        result = subprocess.run(
            ["openclaw", "status", "--json"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            data = json.loads(result.stdout)
            usage = data.get("claude", {}).get("usage_percent")
            if usage is not None:
                logger.info(f"Claude usage: {usage:.1f}%")
                return float(usage)
    except Exception as e:
        logger.warning(f"Could not read Claude usage: {e}")
    return None


def should_fallback_to_mammouth() -> tuple[bool, Optional[str]]:
    """Determine whether to fall back to MammouthAI.

    Returns:
        (should_fallback, reason_or_None)
    """
    from hub_core.fetch.mammouth_ai_usage import get_mammouth_credits

    usage = get_claude_usage_percent()
    if usage is not None and usage > 75:
        reason = f"Claude usage {usage:.1f}% > 75% threshold"
        logger.warning(f"⚠️  FALLBACK TRIGGERED: {reason}")
        return True, reason

    mammouth = get_mammouth_credits()
    if mammouth and mammouth.credits.available <= 0:
        logger.warning("❌ MammouthAI credits exhausted")
        return False, "MammouthAI out of credits"

    return False, None


def try_mammouth_request(
    prompt: str,
    system: Optional[str] = None,
    max_tokens: int = 1000,
    temperature: float = 0.7,
) -> Optional[Dict[str, Any]]:
    """Send a request to MammouthAI as fallback.

    Returns response dict on success, None on failure.
    """
    from hub_core.mammouth.client import get_mammouth_client

    mammouth = get_mammouth_client()
    if not mammouth:
        logger.error("MammouthAI client unavailable")
        return None

    try:
        logger.info("🦣 Fallback: attempting MammouthAI request...")
        result = mammouth.complete(
            prompt=prompt, system=system,
            max_tokens=max_tokens, temperature=temperature, timeout=30,
        )
        if result.get("success"):
            logger.info("✅ MammouthAI request succeeded")
            return result
        logger.error(f"❌ MammouthAI request failed: {result.get('error')}")
        return None
    except Exception as e:
        logger.error(f"❌ MammouthAI request error: {e}")
        return None


def with_mammouth_fallback(func: Callable) -> Callable:
    """Decorator: retry with MammouthAI key on Claude rate limit."""

    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            result = func(*args, **kwargs)
            if isinstance(result, str) and "API rate limit reached" in result:
                logger.warning("Claude API rate limit hit, switching to MammouthAI")
                return _retry_with_mammouth(func, *args, **kwargs)
            if isinstance(result, dict) and result.get("error") and is_rate_limit_error(result["error"]):
                logger.warning("Claude API rate limit hit, switching to MammouthAI")
                return _retry_with_mammouth(func, *args, **kwargs)
            return result
        except Exception as e:
            if is_rate_limit_error(str(e)):
                logger.warning("Claude rate limit exception, switching to MammouthAI")
                return _retry_with_mammouth(func, *args, **kwargs)
            raise

    return wrapper


def _retry_with_mammouth(func: Callable, *args, **kwargs) -> Any:
    mammouth_key = os.getenv("MAMMOUTH_API_KEY")
    if not mammouth_key:
        logger.error("MAMMOUTH_API_KEY not configured")
        return {"error": "Fallback unavailable: MAMMOUTH_API_KEY not configured"}

    original_key = os.getenv("ANTHROPIC_API_KEY")
    try:
        os.environ["ANTHROPIC_API_KEY"] = mammouth_key
        logger.info("Retrying with MammouthAI key...")
        result = func(*args, **kwargs)
        logger.info("✅ MammouthAI fallback succeeded")
        return result
    finally:
        if original_key:
            os.environ["ANTHROPIC_API_KEY"] = original_key
        else:
            os.environ.pop("ANTHROPIC_API_KEY", None)
