"""Entry point for hub-core. Returns all values as a Pydantic model dumpable to dict."""

import json
import os
from datetime import datetime

from loguru import logger

from hub_core.config import SYSTEM_JSON, TOKENS_JSON
from hub_core.dombot_log import DomBotLog
from hub_core.models import HubState, token_or_na

_dbl = DomBotLog(process="hub-core", model=os.getenv("AGENT_MODEL", ""))


def _init_identity() -> str:
    """Load and log agent identity (best-effort; never blocks hub state fetch)."""
    agent_id = os.getenv("AGENT_ID", "")
    if not agent_id:
        return ""
    try:
        from hub_core.security.identity import current_identity, reset_identity
        reset_identity()  # force reload from env
        identity = current_identity()
        _dbl.info(
            "agent:identity",
            f"Agent identified: {identity.identity}",
            role=identity.role.value,
            capabilities=len(identity.capabilities),
        )
        return identity.identity
    except Exception as e:
        logger.warning(f"Identity init skipped: {e}")
        return agent_id


def get_hub_state(*, write_json: bool = True) -> HubState:
    """Fetch all data and return HubState. Optionally write JSON files."""
    from hub_core.fetch.provider_data import get_providers_response
    from hub_core.track.tokens import get_token_stats
    from hub_core.update.status import get_status_response
    from hub_core.update.system_metrics import get_cpu_ram

    identity = _init_identity()
    _dbl.info("hub:refresh", "Fetching hub state", agent=identity or "anonymous")

    providers = get_providers_response(write=write_json)
    status = get_status_response(providers=providers, write=write_json)
    cpu_ram = get_cpu_ram()

    if write_json:
        SYSTEM_JSON.parent.mkdir(parents=True, exist_ok=True)
        SYSTEM_JSON.write_text(
            json.dumps(
                {**cpu_ram.model_dump(), "success": True, "timestamp": datetime.now().isoformat()},
                indent=2,
            )
        )

    stats = get_token_stats()

    # openclaw status provides usage_percent + formatted strings, not absolute counts.
    # Display as "N/A" until a more precise source is wired.
    tokens_today: int | str = "N/A"
    tokens_month: int | str = "N/A"

    if write_json:
        TOKENS_JSON.parent.mkdir(parents=True, exist_ok=True)
        TOKENS_JSON.write_text(json.dumps(stats, indent=2))

    mammouth_credits = providers.mammouth_ai.credits.available if providers.mammouth_ai else None
    claude_usage = stats.get("claude", {}).get("usage_percent", 0)
    _dbl.info(
        "hub:complete",
        "Hub state ready",
        cpu=round(cpu_ram.cpu_percent, 1),
        ram=round(cpu_ram.ram_percent, 1),
        mammouth_credits=mammouth_credits,
        claude_usage=claude_usage,
    )

    return HubState(
        providers=providers,
        status=status,
        cpu_ram=cpu_ram,
        tokens_today=tokens_today,
        tokens_month=tokens_month,
        system_timestamp=datetime.now().isoformat(),
    )


def get_simple_state(*, write_json: bool = True) -> dict:
    """Return a simplified dict view focused on LLM providers and system info."""
    from hub_core.models import CpuRam, ProvidersResponse, StatusResponse

    state = get_hub_state(write_json=write_json)
    providers = state.providers or ProvidersResponse()
    cpu_ram = state.cpu_ram or CpuRam()

    return {
        "providers": {
            "llm_providers": {
                "mammouth_ai": {
                    "credits_available": providers.mammouth_ai.credits.available,
                    "credits_limit": providers.mammouth_ai.credits.limit,
                },
            }
        },
        "system_info": cpu_ram.model_dump(),
        "system_timestamp": state.system_timestamp,
    }


def main() -> HubState:
    """Fetch everything and return all hub values (use .model_dump() for dict)."""
    state = get_hub_state(write_json=True)
    logger.info("Hub state: {} keys", len(state.model_dump()))
    return state


if __name__ == "__main__":
    print(json.dumps(get_simple_state(), indent=2))
