import os
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

SCHEDULER_DIR = Path(__file__).parent
if str(SCHEDULER_DIR) not in sys.path:
    sys.path.insert(0, str(SCHEDULER_DIR))

import scheduler as scheduler_module  # noqa: E402


class _FakeResponse:
    def __init__(self, text: str = "ok") -> None:
        self.text = text

    def raise_for_status(self) -> None:
        return


class _FakeAsyncClient:
    calls = []

    def __init__(self, timeout: int) -> None:
        self.timeout = timeout

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url: str, json: dict):
        _FakeAsyncClient.calls.append((url, json, self.timeout))
        if url.endswith("/chat"):
            return _FakeResponse("agent-result")
        return _FakeResponse("")


class SchedulerTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        scheduler_module.get_settings.cache_clear()
        os.environ["AGENT_URL"] = "http://agent-service:8092"
        os.environ["TELEGRAM_URL"] = "http://telegram:8094"

    async def test_run_skill_validates_and_sends(self) -> None:
        original_client = scheduler_module.httpx.AsyncClient
        _FakeAsyncClient.calls = []
        scheduler_module.httpx.AsyncClient = _FakeAsyncClient
        try:
            await scheduler_module._run_skill({"name": "daily", "prompt": "hello"})
        finally:
            scheduler_module.httpx.AsyncClient = original_client

        self.assertEqual(len(_FakeAsyncClient.calls), 2)
        self.assertEqual(_FakeAsyncClient.calls[0][0], "http://agent-service:8092/chat")
        self.assertEqual(_FakeAsyncClient.calls[0][1], {"message": "hello", "history": []})
        self.assertEqual(
            _FakeAsyncClient.calls[1][1],
            {"text": "[daily]\nagent-result"},
        )

    async def test_run_skill_rejects_invalid_payload(self) -> None:
        original_client = scheduler_module.httpx.AsyncClient
        _FakeAsyncClient.calls = []
        scheduler_module.httpx.AsyncClient = _FakeAsyncClient
        try:
            await scheduler_module._run_skill({"name": "daily"})
        finally:
            scheduler_module.httpx.AsyncClient = original_client
        self.assertEqual(_FakeAsyncClient.calls, [])

    def test_load_skills_validates_yaml(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            (tmp_path / "valid.yaml").write_text(
                "name: morning\ncron: '0 9 * * *'\nprompt: ping\n",
                encoding="utf-8",
            )
            (tmp_path / "disabled.yaml").write_text(
                "name: off\ncron: '0 10 * * *'\nprompt: ignore\nenabled: false\n",
                encoding="utf-8",
            )
            (tmp_path / "invalid.yaml").write_text("name: bad\n", encoding="utf-8")

            skills = scheduler_module._load_skills(tmp_path)

        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].name, "morning")


if __name__ == "__main__":
    unittest.main()
