#!/usr/bin/env python3
"""
Fetch provider data: MammouthAI credits from mammouth_ai_usage.
"""

import sys

from loguru import logger

from hub_core.config import PROVIDERS_JSON
from hub_core.fetch.mammouth_ai_usage import get_mammouth_credits
from hub_core.models import MammouthUsage, ProvidersResponse


def get_providers_response(*, write: bool = True) -> ProvidersResponse:
    """Fetch Mammouth credits (billing API or N/A)."""
    mammouth = get_mammouth_credits() or MammouthUsage()
    response = ProvidersResponse(mammouth_ai=mammouth)
    if write:
        PROVIDERS_JSON.parent.mkdir(parents=True, exist_ok=True)
        PROVIDERS_JSON.write_text(response.model_dump_json(indent=2))
    return response


def main() -> int:
    logger.info("Fetching provider data...")
    get_providers_response(write=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
