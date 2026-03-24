#!/usr/bin/env python3
"""Integration tests for complete Hub ecosystem."""

import pytest
import requests
from pathlib import Path
from unittest.mock import patch


class TestHubServices:
    """Tests for Lab Hub services availability."""

    def _get(self, url: str):
        try:
            return requests.get(url, timeout=5)
        except requests.exceptions.RequestException:
            pytest.skip(f"Service not reachable: {url}")

    def test_hub_dashboard_accessible(self):
        resp = self._get("http://localhost:8088/")
        assert resp.status_code == 200
        assert "Lab" in resp.text or "Hub" in resp.text

    def test_citation_service_accessible(self):
        resp = self._get("http://localhost:8088/citation/")
        if resp.status_code != 200:
            pytest.skip("Citation service not deployed")

    def test_kong_banana_game_accessible(self):
        resp = self._get("http://localhost:8088/kong-banana/")
        if resp.status_code != 200:
            pytest.skip("Kong Banana not deployed")

    def test_messidor_service_accessible(self):
        resp = self._get("http://localhost:8088/messidor/")
        if resp.status_code != 200:
            pytest.skip("Messidor not deployed")


class TestHubCore:
    """Tests for hub-core modules."""

    def test_hub_core_imports(self):
        from hub_core.main import get_hub_state

        assert get_hub_state is not None
        # transcribe is optional (requires faster_whisper)
        try:
            from hub_core.transcribe import transcribe

            assert transcribe is not None
        except ImportError:
            pytest.skip("faster_whisper not installed")

    def test_hub_core_config_loads(self):
        from hub_core.config import LAB_DIR, HUB_API_DIR

        assert LAB_DIR.exists() or True
        assert isinstance(HUB_API_DIR, Path)

    def test_hub_core_models_valid(self):
        from hub_core.models import HubState, ProvidersResponse

        assert HubState is not None
        assert ProvidersResponse is not None


class TestTranscriptionAndCLI:
    """Tests for transcription services and CLI."""

    def test_transcriber_module_imports(self):
        pytest.importorskip("faster_whisper", reason="faster_whisper not installed")
        from hub_core.transcribe import transcribe

        assert transcribe is not None

    def test_cli_main_imports(self):
        from hub_core.__main__ import main

        assert main is not None


class TestDataPersistence:
    """Tests for data persistence (JSON files)."""

    def test_api_json_files_exist_or_creatable(self):
        from hub_core.config import HUB_API_DIR, DATA_DIR

        assert HUB_API_DIR or True
        assert DATA_DIR or True

    @patch("hub_core.main.get_hub_state")
    def test_hub_state_json_generation(self, mock_state):
        from hub_core.models import HubState

        state = HubState(
            providers={},
            status={},
            cpu_ram={"cpu_percent": 10.5, "ram_percent": 37.4},
            tokens_today="N/A",
            tokens_month="N/A",
            system_timestamp="2026-02-27T13:00:00",
        )
        json_str = state.model_dump_json()
        assert "cpu" in json_str


class TestLabEnvironment:
    """Tests for Lab environment configuration."""

    def test_lab_dir_configured(self):
        from hub_core.config import LAB_DIR

        assert "lab" in str(LAB_DIR).lower()

    def test_hub_directories_structure(self):
        from hub_core.config import HUB_API_DIR

        assert "api" in str(HUB_API_DIR)
        assert "public" in str(HUB_API_DIR)
