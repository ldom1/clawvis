# OpenClaw — Telegram / Discord and voice transcription (Clawvis)

This guide connects **messaging channels** (Telegram, Discord) managed by **OpenClaw** to audio transcription, using **Faster Whisper** already integrated in `hub-core` (no API key).

Upstream reference: [Audio and Voice Notes](https://docs.openclaw.ai/audio).

---

## Overview

| Layer | Role |
|--------|------|
| **OpenClaw** | Receives voice on Telegram/Discord, downloads media, calls `tools.media.audio` |
| **`tools.media.audio`** | Model chain (API or CLI); transcript replaces message body for the agent |
| **Clawvis `hub_core transcribe`** | Local CLI: Faster Whisper via `uv run` in `hub-core/` |

Same **`tools.media.audio`** configuration for **all** channels: once enabled, Telegram voice notes **and** Discord (per what your OpenClaw version supports for Discord) use the same pipeline.

---

## 1. Local prerequisites

```bash
cd /path/to/clawvis/hub-core
uv sync
uv pip install faster-whisper
```

Manual test:

```bash
uv run python -m hub_core transcribe /path/to/note.ogg -l fr -m base
```

Text should print to stdout.

---

## 2. Wire Telegram or Discord (OpenClaw)

Bot connections and tokens live in OpenClaw config (often `~/.openclaw/openclaw.json` + secrets / auth profiles). Follow OpenClaw docs to:

- create the Telegram bot / Discord application;
- set `channels.telegram` / `channels.discord` (exact names per your OpenClaw version);
- restart the gateway: `openclaw gateway restart`.

Without channels configured, no transcription will run on the messenger side.

---

## 3. Enable transcription (automatic or manual)

### Option A — Clawvis script (recommended)

From the Clawvis repo root:

```bash
# JSON fragment + instructions (single script)
bash scripts/transcribe-audio.sh --config

# Backup openclaw.json then merge (if absent, same CLI entry)
bash scripts/transcribe-audio.sh --config --apply
```

The script only runs **`uv run python -m hub_core openclaw-audio-config`** in `hub-core/`; all JSON merging is in [`hub_core/openclaw_audio_config.py`](../../hub-core/hub_core/openclaw_audio_config.py).

Optional variable: `OPENCLAW_JSON=/path/to/openclaw.json`.

Then:

```bash
openclaw gateway restart
```

The single script is [`scripts/transcribe-audio.sh`](../../scripts/transcribe-audio.sh): normal usage calls `uv run python -m hub_core transcribe` with the OpenClaw file (`{{MediaPath}}`); `--config` generates / merges `tools.media.audio`.

Optional environment variables for the **process** launched by OpenClaw (if you export them before `gateway start` or via your systemd unit):

| Variable | Default | Role |
|----------|---------|------|
| `TRANSCRIBE_LANG` | `fr` | Whisper language |
| `TRANSCRIBE_MODEL` | `base` | `tiny`, `base`, `small`, etc. |

### Option B — Cloud provider (no local Whisper)

You can instead (or in addition, before/after the CLI) use OpenAI, Deepgram, Mistral Voxtral, etc., as in [OpenClaw audio docs](https://docs.openclaw.ai/audio). Configure `models` with `provider` + API keys per docs.

### Option C — Manual merge

If you prefer editing by hand, add under `tools.media` an `audio` block with a `"type": "cli"` model pointing to the **absolute** path of `transcribe-audio.sh` and `"args": ["{{MediaPath}}"]`.

---

## 4. Telegram groups and mentions

For **groups** with `requireMention: true`, OpenClaw may run **transcription first** to detect the mention in voice. See *Mention Detection in Groups* on [docs.openclaw.ai/audio](https://docs.openclaw.ai/audio).

---

## 5. Clawvis skills integration

The **project-init** skill expects text; for a Telegram voice, the typical flow is: **OpenClaw transcribes** → message body seen by the agent contains the transcript → the skill can continue (see [`skills/project-init/SKILL.md`](../../skills/project-init/SKILL.md)).

Manual mode outside OpenClaw: `uv run python -m hub_core transcribe <file>`.

---

## 6. Quick troubleshooting

| Symptom | Lead |
|---------|------|
| No transcript | Check `tools.media.audio.enabled`, gateway logs `--verbose`, `faster-whisper` installed |
| Timeout | Increase `timeoutSeconds` (Whisper CPU on large files) |
| Permission / PATH | Use **absolute** path for CLI model `command` |
| Discord only | Confirm in your OpenClaw version docs that Discord audio uses the same `tools.media.audio` pipeline |

---

## See also

- [`scripts/transcribe-audio.sh`](../../scripts/transcribe-audio.sh) — transcription + `--config` / `--config --apply`  
- [`hub-core/hub_core/transcribe/`](../../hub-core/hub_core/transcribe/) — Faster Whisper implementation
