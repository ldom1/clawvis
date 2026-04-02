#!/usr/bin/env python3
"""Audio transcription using Faster Whisper (open-source, local). No API key required.
For OpenClaw voice (Telegram/Discord): `scripts/transcribe-audio.sh` (transcript + `--config`).
See `docs/guides/openclaw-transcribe-channels.md`."""

from pathlib import Path
from typing import Optional

from loguru import logger

try:
    from faster_whisper import WhisperModel
except ImportError:
    WhisperModel = None


def transcribe(
    audio_path: str, language: str = "fr", model_size: str = "base"
) -> Optional[str]:
    """
    Transcribe audio file to text using Faster Whisper.

    Args:
        audio_path: Path to audio file (supports mp3, wav, ogg, flac, m4a)
        language: Language code (default: "fr" for French)
        model_size: Model size - "tiny", "base", "small", "medium", "large"

    Returns:
        Transcribed text or None if error
    """
    path = Path(audio_path)

    if not path.exists():
        logger.error("Audio file not found: {}", audio_path)
        return None
    if WhisperModel is None:
        logger.error("faster-whisper not installed. Run: uv pip install faster-whisper")
        return None

    try:
        logger.info("Transcribing: {} (model: {})", path.name, model_size)

        # Load model (downloads if first time, ~500MB for base)
        model = WhisperModel(model_size, device="cpu", compute_type="int8")

        # Transcribe
        segments, info = model.transcribe(str(path), language=language)

        # Collect text
        text = "".join(segment.text for segment in segments)

        logger.info("✅ Transcribed ({:.1f}s)", info.duration)
        return text.strip()

    except Exception as e:
        logger.error("Transcription failed: {}", e)
        return None
