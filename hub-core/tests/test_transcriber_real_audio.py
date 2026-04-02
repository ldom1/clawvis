#!/usr/bin/env python3
import re
import unicodedata
from pathlib import Path

import pytest

from hub_core.transcribe import transcribe


def test_transcribe_real_audio_example():
    pytest.importorskip(
        "faster_whisper",
        reason="Install: uv sync --directory hub-core --extra transcribe",
    )
    audio = Path(__file__).parent / "data" / "audio_example.ogg"
    assert audio.exists()

    expected_txt = "Qu'est ce que Kimi.com ? Est qu'est ce que Kimi Claw ? il y a écrit que je peux créer un Kimi Claw en 1 seconde euh ... comment ca fonctionne"

    text = transcribe(str(audio), language="fr", model_size="tiny")
    if text is None:
        pytest.skip("Whisper model/load failed (network or optional runtime)")
    assert isinstance(text, str)
    assert text.strip()

    def norm(s: str) -> str:
        s = unicodedata.normalize("NFD", s.lower())
        s = "".join(c for c in s if unicodedata.category(c) != "Mn")
        s = re.sub(r"[^a-z0-9\s]", " ", s)
        return re.sub(r"\s+", " ", s).strip()

    nt, ne = norm(text), norm(expected_txt)
    for frag in ("kimi com", "comment", "fonctionne", "seconde"):
        assert frag in nt, f"Missing {frag!r}. Expected around: {ne!r}. Got: {nt!r}"
