"""
Wikipedia 'On This Day' via Wikimedia feed API.
No invented data: returns None if the API fails or has no usable event.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any

FEED_BASE = "https://api.wikimedia.org/feed/v1/wikipedia"
DEFAULT_LANG = "en"
USER_AGENT = (
    "ClawvisMorningBriefing/1.0 (https://github.com/ldom1/clawvis; morning-briefing skill)"
)


@dataclass
class OnThisDayEvent:
    year: int | None
    text: str
    url: str | None


def _desktop_url_from_page(page: dict[str, Any]) -> str | None:
    urls = page.get("content_urls") or {}
    desktop = urls.get("desktop") or {}
    mobile = urls.get("mobile") or {}
    u = desktop.get("page") or mobile.get("page")
    if isinstance(u, str) and u.startswith("http"):
        return u
    return None


def _pick_best_event(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Heuristic: prefer substantive text; tie-break by earlier calendar year (more 'historical')."""
    usable: list[tuple[int, int, dict[str, Any]]] = []
    for ev in events:
        text = (ev.get("text") or "").strip()
        if len(text) < 35:
            continue
        y = ev.get("year")
        try:
            yi = int(y) if y is not None else None
        except (TypeError, ValueError):
            yi = None
        score_len = min(len(text), 800)
        # Sort: higher score_len first; same length → smaller year first (e.g. 1066 before 2019).
        year_key = yi if yi is not None else 99999
        usable.append((score_len, year_key, ev))
    if not usable:
        return None
    usable.sort(key=lambda t: (-t[0], t[1]))
    return usable[0][2]


def _event_url(ev: dict[str, Any]) -> str | None:
    pages = ev.get("pages") or []
    for p in pages:
        if not isinstance(p, dict):
            continue
        u = _desktop_url_from_page(p)
        if u:
            return u
    return None


def _normalize_year(raw: Any) -> int | None:
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def fetch_on_this_day(
    *,
    when: datetime | None = None,
    lang: str | None = None,
    timeout: float = 10.0,
) -> OnThisDayEvent | None:
    """
    GET /feed/v1/wikipedia/{lang}/onthisday/events/{month}/{day}
    """
    now = when or datetime.now()
    language = (lang or DEFAULT_LANG).strip().lower() or DEFAULT_LANG
    url = f"{FEED_BASE}/{language}/onthisday/events/{now.month}/{now.day}"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, TimeoutError, OSError):
        return None

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None

    events = data.get("events")
    if not isinstance(events, list) or not events:
        return None

    ev = _pick_best_event([e for e in events if isinstance(e, dict)])
    if not ev:
        return None

    text = re.sub(r"\s+", " ", (ev.get("text") or "").strip())
    if len(text) < 35:
        return None

    year = _normalize_year(ev.get("year"))
    page_url = _event_url(ev)
    return OnThisDayEvent(year=year, text=text, url=page_url)
