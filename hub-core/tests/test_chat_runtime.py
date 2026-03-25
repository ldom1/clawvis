"""Tests for hub_core.chat_runtime stream error tokens."""

from hub_core.chat_runtime import _stream_error_chunk


def test_stream_error_chunk_401():
    assert _stream_error_chunk(401, b"{}") == "[CLAWVIS:AUTH]"


def test_stream_error_chunk_auth_in_json():
    body = b'{"type":"error","error":{"type":"authentication_error","message":"x"}}'
    assert _stream_error_chunk(403, body) == "[CLAWVIS:AUTH]"


def test_stream_error_chunk_other():
    assert _stream_error_chunk(429, b"too many") == "[CLAWVIS:HTTP:429]"
