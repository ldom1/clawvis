#!/usr/bin/env python3
"""
Usage status from providers.json: Mammouth credits.
"""

import json

from hub_core.config import PROVIDERS_JSON, STATUS_JSON
from hub_core.models import MammouthUsage, ProvidersResponse, StatusResponse


def _read_providers_file():
    try:
        with open(PROVIDERS_JSON) as f:
            return json.load(f)
    except Exception:
        return {}


def get_mammouth_usage_from_file() -> MammouthUsage:
    """From providers.json."""
    data = _read_providers_file()
    m = data.get("mammouth_ai", {})
    if m:
        from hub_core.models import MammouthCredits

        c = m.get("credits", {})
        return MammouthUsage(
            credits=MammouthCredits(
                available=c.get("available", "N/A"),
                limit=c.get("limit", "N/A"),
                currency=c.get("currency", "USD"),
            ),
            subscription=m.get("subscription", "N/A"),
            additional=m.get("additional", "N/A"),
            last_updated=m.get("last_updated", "N/A"),
        )
    return MammouthUsage()


def get_status_response(
    providers: ProvidersResponse | None = None, *, write: bool = True
) -> StatusResponse:
    """Build status from providers (Mammouth credits)."""
    mammouth = (
        providers.mammouth_ai
        if providers is not None
        else get_mammouth_usage_from_file()
    )
    response = StatusResponse(mammouth_usage=mammouth)
    if write:
        STATUS_JSON.parent.mkdir(parents=True, exist_ok=True)
        STATUS_JSON.write_text(response.model_dump_json(indent=2))
    return response


def main() -> int:
    get_status_response(write=True)
    return 0


if __name__ == "__main__":
    exit(main())
