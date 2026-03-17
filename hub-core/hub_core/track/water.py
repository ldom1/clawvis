#!/usr/bin/env python3
"""
Water consumption tracking based on API token usage.

Reference:
- GPT-3: ~500ml water per million tokens (training)
- ChatGPT inference: ~0.5-1L per million tokens (including cooling)
- Industry estimate: ~600ml per million tokens for inference

Using conservative estimate: 500ml per million tokens
"""

import json
import subprocess
from datetime import datetime
from typing import Any, Dict

from loguru import logger

from hub_core.config import SYSTEM_JSON

# Water consumption constants
WATER_PER_MILLION_TOKENS_ML = 500  # milliliters


def get_token_usage() -> Dict[str, int]:
    """Fetch total token usage from OpenClaw sessions"""
    try:
        # Get session data from OpenClaw
        result = subprocess.run(
            ["openclaw", "sessions", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return {"total": 0, "claude": 0}

        data = json.loads(result.stdout)
        sessions = data.get("sessions", [])

        # Sum tokens from all Claude sessions
        total_tokens = 0
        for session in sessions:
            if "totalTokens" in session:
                tokens = session.get("totalTokens", 0)
                total_tokens += tokens

        return {"total": total_tokens, "claude": total_tokens}

    except Exception as e:
        logger.error("Error fetching token usage: {}", e)
        return {"total": 0, "claude": 0}


def calculate_water_usage(tokens: int) -> Dict[str, Any]:
    """Calculate water usage from token count"""
    # Water in milliliters
    water_ml = (tokens / 1_000_000) * WATER_PER_MILLION_TOKENS_ML

    # Convert to liters
    water_liters = water_ml / 1000

    # Convert to gallons (US)
    water_gallons = water_liters * 0.264172

    # Estimate water bottle equivalents (500ml bottle)
    water_bottles = water_ml / 500

    return {
        "tokens": tokens,
        "water_ml": round(water_ml, 2),
        "water_liters": round(water_liters, 3),
        "water_gallons": round(water_gallons, 3),
        "water_bottles": round(water_bottles, 2),
        "water_label": format_water(water_ml),
    }


def format_water(ml: float) -> str:
    """Format water consumption in human-readable format"""
    if ml < 1000:
        return f"{ml:.0f}ml"
    elif ml < 1_000_000:
        return f"{ml / 1000:.2f}L"
    else:
        return f"{ml / 1_000_000:.2f}M liters"


def update_system_json():
    """Update system.json with water consumption data"""
    try:
        # Read current system.json
        if SYSTEM_JSON.exists():
            with open(SYSTEM_JSON) as f:
                system_data = json.load(f)
        else:
            system_data = {"success": False, "cpu_percent": 0, "ram_percent": 0}

        # Get token usage and calculate water
        tokens = get_token_usage()
        water_data = calculate_water_usage(tokens["total"])

        # Add water consumption to system data
        system_data["water_consumption"] = water_data
        system_data["timestamp"] = datetime.now().isoformat()

        # Write back
        SYSTEM_JSON.parent.mkdir(parents=True, exist_ok=True)
        with open(SYSTEM_JSON, "w") as f:
            json.dump(system_data, f, indent=2)

        logger.info("Water consumption updated: {}", water_data["water_label"])
        return water_data

    except Exception as e:
        logger.error("Error updating water consumption: {}", e)
        return None


def main():
    """Main entry point"""
    result = update_system_json()
    if result:
        logger.info(
            "{} tokens → {} ({} × 500ml bottles)",
            result["tokens"],
            result["water_label"],
            result["water_bottles"],
        )


if __name__ == "__main__":
    main()
