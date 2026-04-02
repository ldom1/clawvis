#!/usr/bin/env python3
"""MammouthAI credits: key/info (proxy) or v1/account/billing (direct)."""

import datetime
from typing import Optional

import requests
from loguru import logger

from hub_core.config import MAMMOUTH_API_KEY
from hub_core.models import MammouthCredits, MammouthUsage

BASE = "https://api.mammouth.ai"


def get_mammouth_credits() -> Optional[MammouthUsage]:
    if not MAMMOUTH_API_KEY:
        return None
    try:
        r = requests.get(
            f"{BASE}/key/info?key={requests.utils.quote(MAMMOUTH_API_KEY, safe='')}",
            headers={"Authorization": f"Bearer {MAMMOUTH_API_KEY}"},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        d = r.json()
        info = d.get("info", d)
        spend = float(info.get("spend", 0) or 0)
        limit = float(
            info.get("max_budget", info.get("metadata", {}).get("base_budget", 2)) or 2
        )
        avail = max(0, limit - spend)
        currency = "EUR"
        sym = "€" if currency == "EUR" else "$" if currency == "USD" else ""
        sub = (
            f"{sym}{avail:.2f} / {sym}{limit:.2f}"
            if sym
            else f"{avail:.2f} {currency} / {limit:.2f} {currency}"
        )
        return MammouthUsage(
            credits=MammouthCredits(available=avail, limit=limit, currency=currency),
            subscription=sub,
            additional="N/A",
            last_updated=datetime.datetime.now().strftime("%H:%M:%S"),
        )
    except Exception as e:
        logger.warning("MammouthAI: {}", e)
        return None
