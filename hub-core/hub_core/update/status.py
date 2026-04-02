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
    return MammouthUsage.from_providers_mammouth_block(data.get("mammouth_ai") or {})


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
