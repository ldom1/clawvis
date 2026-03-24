#!/usr/bin/env python3
"""Tests for audio transcription module."""

from unittest.mock import patch, MagicMock


class TestTranscriber:
    """Tests for audio transcription."""

    def _transcribe(self, *args, **kwargs):
        from hub_core.transcribe import transcribe

        return transcribe(*args, **kwargs)

    def test_transcribe_file_not_found(self):
        """Test that transcribe returns None for missing file."""
        result = self._transcribe("/nonexistent/audio.mp3")
        assert result is None

    @patch("hub_core.transcribe.transcriber.WhisperModel", None)
    def test_transcribe_none_when_whispermodel_none(self, tmp_path):
        """If faster-whisper is missing, transcribe should return None."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 100)
        result = self._transcribe(str(audio_file))
        assert result is None

    def test_transcribe_returns_string(self, tmp_path):
        """Test that transcribe returns a string (or None)."""
        # Create a dummy audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 100)  # Minimal WAV header

        result = self._transcribe(str(audio_file))
        assert result is None or isinstance(result, str)

    @patch("hub_core.transcribe.transcriber.WhisperModel")
    def test_transcribe_with_mock_model(self, mock_whisper, tmp_path):
        """Test transcription with mocked Whisper model."""
        # Create dummy audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 100)

        # Mock the model
        mock_model = MagicMock()
        mock_whisper.return_value = mock_model

        # Mock segments
        mock_segment = MagicMock()
        mock_segment.text = "This is a test transcription."
        mock_model.transcribe.return_value = ([mock_segment], MagicMock(duration=5.0))

        result = self._transcribe(str(audio_file))
        assert result == "This is a test transcription."

    @patch("hub_core.transcribe.transcriber.WhisperModel")
    def test_transcribe_handles_exception(self, mock_whisper, tmp_path):
        """Test that transcribe handles exceptions gracefully."""
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 100)

        mock_whisper.side_effect = Exception("Model load failed")
        result = self._transcribe(str(audio_file))
        assert result is None

    def test_transcribe_language_parameter(self):
        """Test that language parameter is accepted."""
        # Should not raise error even if file doesn't exist
        # (function returns None for missing files)
        result = self._transcribe("/fake.mp3", language="en")
        assert result is None

    def test_transcribe_model_size_parameter(self):
        """Test that model_size parameter is accepted."""
        result = self._transcribe("/fake.mp3", model_size="tiny")
        assert result is None

    @patch("hub_core.transcribe.transcriber.WhisperModel")
    def test_transcribe_multiple_segments(self, mock_whisper, tmp_path):
        """Test transcription with multiple audio segments."""
        audio_file = tmp_path / "multi.wav"
        audio_file.write_bytes(b"RIFF" + b"\x00" * 100)

        mock_model = MagicMock()
        mock_whisper.return_value = mock_model

        # Multiple segments
        seg1 = MagicMock()
        seg1.text = "Hello "
        seg2 = MagicMock()
        seg2.text = "world!"

        mock_model.transcribe.return_value = ([seg1, seg2], MagicMock(duration=3.0))

        result = self._transcribe(str(audio_file))
        assert result == "Hello world!"
