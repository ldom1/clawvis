#!/usr/bin/env python3
"""CLI for hub_core (status, setup-runtime, setup-sync-apply)."""

import argparse
import json
import sys

from loguru import logger

from hub_core.main import get_hub_state
from hub_core.setup_runtime import run_setup_runtime
from hub_core.setup_sync import apply_sync_check


def cmd_status(args):
    logger.info("Fetching hub state...")
    state = get_hub_state(write_json=True)
    print(state.model_dump_json(indent=2))
    return 0


def cmd_setup_sync_apply(args):
    out = apply_sync_check()
    actions = out.get("actions") or []
    for a in actions:
        print(f"[warn] clawvis setup-sync: {a}", file=sys.stderr)
    if getattr(args, "verbose", False):
        print(json.dumps(out, indent=2))
    return 0


def cmd_setup_runtime(args):
    payload = run_setup_runtime(
        provider=args.provider,
        claude_api_key=args.claude_api_key,
        mistral_api_key=args.mistral_api_key,
        cli_tool=args.cli_tool,
        non_interactive=args.non_interactive,
    )
    print(json.dumps(payload, indent=2))
    if payload.get("configured"):
        print("Runtime configured. Redemarre les services pour appliquer.")
        return 0
    print("Runtime partially configured. Verifie les credentials.")
    return 1


def main():
    parser = argparse.ArgumentParser(
        prog="hub_core",
        description="Clawvis hub_core — status, runtime setup",
    )
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    parser_status = subparsers.add_parser("status", help="Show hub status")
    parser_status.set_defaults(func=cmd_status)

    parser_sync = subparsers.add_parser(
        "setup-sync-apply",
        help="Apply idempotent skills/memory sync (PRIMARY_AI_PROVIDER from .env)",
    )
    parser_sync.add_argument("-v", "--verbose", action="store_true")
    parser_sync.set_defaults(func=cmd_setup_sync_apply)

    parser_setup_runtime = subparsers.add_parser(
        "setup-runtime", help="Setup primary AI runtime and write .env"
    )
    parser_setup_runtime.add_argument(
        "--provider", choices=["claude", "mistral", "cli"]
    )
    parser_setup_runtime.add_argument("--claude-api-key")
    parser_setup_runtime.add_argument("--mistral-api-key")
    parser_setup_runtime.add_argument("--cli-tool")
    parser_setup_runtime.add_argument(
        "--non-interactive", action="store_true",
        help="Do not prompt; requires explicit args",
    )
    parser_setup_runtime.set_defaults(func=cmd_setup_runtime)

    args = parser.parse_args()
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
