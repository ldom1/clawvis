#!/usr/bin/env python3
"""CLI for hub_core - DomBot's Hub Tools."""

import argparse
import json
import sys
from pathlib import Path

from loguru import logger

from hub_core.main import get_hub_state
from hub_core.services import ServiceManager
from hub_core.git_sync import cli as git_sync_cli


def cmd_status(args):
    """Show hub status."""
    logger.info("Fetching hub state...")
    state = get_hub_state(write_json=True)
    print(state.model_dump_json(indent=2))
    return 0


def cmd_transcribe(args):
    """Transcribe audio file."""
    try:
        from hub_core.transcribe import transcribe
    except ImportError:
        logger.error("faster_whisper not installed. Run: uv pip install faster-whisper")
        return 1

    if not args.file:
        logger.error("Audio file required")
        return 1

    logger.info("Transcribing: {}", args.file)
    text = transcribe(
        args.file,
        language=args.language,
        model_size=args.model
    )
    
    if text:
        print(text)
        if args.output:
            Path(args.output).write_text(text)
            logger.info("Transcript saved to: {}", args.output)
        return 0
    else:
        logger.error("Transcription failed")
        return 1


def cmd_services(args):
    """Manage Lab services (start/stop/status)."""
    if args.action == "status":
        if args.service == "all":
            services = ServiceManager.get_all_services()
            print("\n📊 Lab Services Status:\n")
            total_ram = 0
            for service_id, status in services.items():
                running = "✅" if status.get("running") else "❌"
                ram = status.get("ram_mb", 0)
                total_ram += ram if status.get("running") else 0
                print(f"{running} {status.get('name')}")
                print(f"   Port: {status.get('port')} | RAM: {ram}MB")
                if status.get("error"):
                    print(f"   Error: {status.get('error')}")
                print()
            print(f"📊 Total RAM (running): ~{int(total_ram)}MB\n")
        else:
            status = ServiceManager.get_status(args.service)
            print("\n" + str(status) + "\n")
        return 0
    
    elif args.action == "start":
        result = ServiceManager.start(args.service)
        print(result)
        return 0 if result.get("success") else 1
    
    elif args.action == "stop":
        result = ServiceManager.stop(args.service)
        print(result)
        return 0 if result.get("success") else 1
    
    elif args.action == "restart":
        result = ServiceManager.restart(args.service)
        print(result)
        return 0 if result.get("success") else 1
    
    return 1


def cmd_git(args):
    """Run Lab git sync/status (wraps git-sync.sh + git-status.json)."""
    sync = args.action == "sync"
    code = git_sync_cli(sync=sync)
    # Re-read the JSON to print it (nice UX if script wrote it)
    from hub_core.git_sync import GIT_STATUS_JSON  # local import to avoid cycles

    if GIT_STATUS_JSON.exists():
        try:
            payload = json.loads(GIT_STATUS_JSON.read_text())
            print(json.dumps(payload, indent=2))
        except Exception:  # pragma: no cover - best-effort print
            pass
    return code


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="hub_core",
        description="DomBot's Hub Core - AI news, transcription, system monitoring"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # status command
    parser_status = subparsers.add_parser("status", help="Show hub status")
    parser_status.set_defaults(func=cmd_status)
    
    # transcribe command
    parser_transcribe = subparsers.add_parser("transcribe", help="Transcribe audio")
    parser_transcribe.add_argument("file", nargs="?", help="Audio file path")
    parser_transcribe.add_argument("-l", "--language", default="fr", help="Language (default: fr)")
    parser_transcribe.add_argument("-m", "--model", default="base", help="Model size (tiny, base, small, medium, large)")
    parser_transcribe.add_argument("-o", "--output", help="Output text file")
    parser_transcribe.set_defaults(func=cmd_transcribe)
    
    # services command
    parser_services = subparsers.add_parser("services", help="Manage Lab services (start/stop/status)")
    parser_services.add_argument("action", choices=["status", "start", "stop", "restart"], help="Action")
    parser_services.add_argument(
        "-s",
        "--service",
        default="all",
        help="Service id (debate, messidor, optimizer, epidemie, melodimage, poetic_shield, or 'all')",
    )
    parser_services.set_defaults(func=cmd_services)

    # git command
    parser_git = subparsers.add_parser("git", help="Git sync & status for Lab repos")
    parser_git.add_argument(
        "action",
        choices=["status", "sync"],
        help="Only update status JSON, or run git-sync.sh then update status",
    )
    parser_git.set_defaults(func=cmd_git)
    
    args = parser.parse_args()
    
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
