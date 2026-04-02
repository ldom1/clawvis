"""tools.media.audio JSON pour OpenClaw (fragment + fusion openclaw.json)."""

from __future__ import annotations

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

MAX_BYTES = 20971520
TIMEOUT_SEC = 180


def _cli_model(wrapper: str) -> dict:
    return {
        "type": "cli",
        "command": wrapper,
        "args": ["{{MediaPath}}"],
        "timeoutSeconds": TIMEOUT_SEC,
    }


def audio_block(wrapper: str) -> dict:
    return {
        "enabled": True,
        "maxBytes": MAX_BYTES,
        "timeoutSeconds": TIMEOUT_SEC,
        "models": [_cli_model(wrapper)],
    }


def fragment_document(wrapper: str) -> dict:
    return {"tools": {"media": {"audio": audio_block(wrapper)}}}


def merge_into(path: Path, wrapper: str) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    tools = data.setdefault("tools", {})
    media = tools.setdefault("media", {})
    audio = media.setdefault("audio", {})
    audio["enabled"] = True
    audio.setdefault("maxBytes", MAX_BYTES)
    audio.setdefault("timeoutSeconds", TIMEOUT_SEC)
    models = audio.setdefault("models", [])
    cli = _cli_model(wrapper)
    if not any(
        isinstance(m, dict) and m.get("type") == "cli" and m.get("command") == wrapper
        for m in models
    ):
        models.insert(0, cli)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _print_guide(wrapper_path: Path) -> None:
    root = wrapper_path.resolve().parent.parent
    print(
        f"""=== Clawvis → OpenClaw audio (local Whisper via hub_core) ===

1) Installer le modèle local (une fois) :
     cd {root}/hub-core && uv sync && uv pip install faster-whisper

2) Brancher Telegram et/ou Discord — https://docs.openclaw.ai/

3) Fragment JSON tools.media.audio :
""",
        file=sys.stderr,
        end="",
    )


def run_openclaw_audio_config(
    wrapper: str,
    *,
    apply: bool,
    json_path: Path | None,
) -> int:
    wp = str(Path(wrapper).resolve())
    cfg_path = json_path or Path(
        os.environ.get("OPENCLAW_JSON", str(Path.home() / ".openclaw" / "openclaw.json"))
    )

    _print_guide(Path(wrapper))
    print(file=sys.stderr)

    if not apply:
        print(json.dumps(fragment_document(wp), indent=2))
        print(file=sys.stderr)
        print(f"   Ce script (référence openclaw.json) : {wp}", file=sys.stderr)
        print(file=sys.stderr)
        print(f"Fusion automatique :  bash {wp} --config --apply", file=sys.stderr)
        print(
            "(ou OPENCLAW_JSON=... ; backup .bak.* à côté du json)",
            file=sys.stderr,
        )
        return 0

    cfg_path = cfg_path.expanduser()
    if not cfg_path.is_file():
        print(f"Missing {cfg_path}", file=sys.stderr)
        return 1
    stamp = datetime.now().strftime("%Y%m%d%H%M%S")
    bak = Path(str(cfg_path) + f".bak.{stamp}")
    shutil.copy2(cfg_path, bak)
    merge_into(cfg_path, wp)
    print(
        f"Merged CLI transcribe into {cfg_path} (backup: {bak}). "
        "Restart: openclaw gateway restart",
        file=sys.stderr,
    )
    print(file=sys.stderr)
    print("4) Redémarrer :  openclaw gateway restart", file=sys.stderr)
    return 0
