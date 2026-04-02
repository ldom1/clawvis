#!/usr/bin/env python3
"""CLI for hub_core (status, transcribe, openclaw-audio-config, setup-runtime)."""

import argparse
import json
import sys
from pathlib import Path

from loguru import logger

from hub_core.main import get_hub_state
from hub_core.openclaw_audio_config import run_openclaw_audio_config
from hub_core.setup_runtime import run_setup_runtime


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
    text = transcribe(args.file, language=args.language, model_size=args.model)

    if text:
        print(text)
        if args.output:
            Path(args.output).write_text(text)
            logger.info("Transcript saved to: {}", args.output)
        return 0
    else:
        logger.error("Transcription failed")
        return 1


def cmd_openclaw_audio_config(args):
    """Print or merge OpenClaw tools.media.audio fragment."""
    return run_openclaw_audio_config(
        args.wrapper,
        apply=args.apply,
        json_path=Path(args.json) if args.json else None,
    )


def cmd_setup_runtime(args):
    """Interactive setup for primary AI runtime (.env)."""
    payload = run_setup_runtime(
        provider=args.provider,
        claude_api_key=args.claude_api_key,
        mistral_api_key=args.mistral_api_key,
        openclaw_base_url=args.openclaw_base_url,
        openclaw_api_key=args.openclaw_api_key,
        non_interactive=args.non_interactive,
    )
    print(json.dumps(payload, indent=2))
    if payload.get("configured"):
        print("Runtime configured. Redemarre les services pour appliquer.")
        return 0
    print("Runtime partially configured. Verifie les credentials.")
    return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="hub_core",
        description="Clawvis hub_core — status, transcription, runtime setup",
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # status command
    parser_status = subparsers.add_parser("status", help="Show hub status")
    parser_status.set_defaults(func=cmd_status)

    # transcribe command
    parser_transcribe = subparsers.add_parser("transcribe", help="Transcribe audio")
    parser_transcribe.add_argument("file", nargs="?", help="Audio file path")
    parser_transcribe.add_argument(
        "-l", "--language", default="fr", help="Language (default: fr)"
    )
    parser_transcribe.add_argument(
        "-m",
        "--model",
        default="base",
        help="Model size (tiny, base, small, medium, large)",
    )
    parser_transcribe.add_argument("-o", "--output", help="Output text file")
    parser_transcribe.set_defaults(func=cmd_transcribe)

    parser_oac = subparsers.add_parser(
        "openclaw-audio-config",
        help="Fragment / merge tools.media.audio for OpenClaw (Whisper local)",
    )
    parser_oac.add_argument(
        "--wrapper",
        required=True,
        help="Absolute path to scripts/transcribe-audio.sh",
    )
    parser_oac.add_argument(
        "--apply",
        action="store_true",
        help="Merge into openclaw.json (backup first)",
    )
    parser_oac.add_argument(
        "--json",
        help="openclaw.json path (default: OPENCLAW_JSON or ~/.openclaw/openclaw.json)",
    )
    parser_oac.set_defaults(func=cmd_openclaw_audio_config)

    # setup-runtime command
    parser_setup_runtime = subparsers.add_parser(
        "setup-runtime", help="Setup primary AI runtime and write .env"
    )
    parser_setup_runtime.add_argument(
        "--provider", choices=["claude", "mistral", "openclaw"]
    )
    parser_setup_runtime.add_argument("--claude-api-key")
    parser_setup_runtime.add_argument("--mistral-api-key")
    parser_setup_runtime.add_argument("--openclaw-base-url")
    parser_setup_runtime.add_argument("--openclaw-api-key")
    parser_setup_runtime.add_argument(
        "--non-interactive",
        action="store_true",
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
