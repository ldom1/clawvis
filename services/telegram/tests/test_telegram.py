from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path
from unittest import mock
from unittest.mock import AsyncMock, MagicMock, patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import TelegramSettings, get_settings  # noqa: E402
from core.models import (  # noqa: E402
    AgentChatRequest,
    OutcomingMessage,
    incoming_from_update,
)


def _std_env() -> dict[str, str]:
    return {
        "AGENT_URL": "http://agent:8092",
        "TELEGRAM_BOT_TOKEN": "x:y",
        "TELEGRAM_CHAT_ID": "1",
        "TELEGRAM_SEND_PORT": "8094",
    }


class TestModelsAndConfig(unittest.TestCase):
    def setUp(self) -> None:
        get_settings.cache_clear()

    def tearDown(self) -> None:
        get_settings.cache_clear()

    @mock.patch.dict(os.environ, _std_env(), clear=True)
    def test_get_settings(self) -> None:
        s = get_settings()
        self.assertEqual(s.agent_url, "http://agent:8092")
        self.assertEqual(s.chat_id, 1)
        self.assertEqual(s.send_port, 8094)
        self.assertFalse(s.stub_mode)

    @mock.patch.dict(os.environ, {**_std_env(), "TELEGRAM_BOT_TOKEN": ""}, clear=True)
    def test_get_settings_stub_mode(self) -> None:
        s = get_settings()
        self.assertTrue(s.stub_mode)

    def test_incoming_from_update_parses(self) -> None:
        update = MagicMock()
        update.message = MagicMock()
        update.message.text = "ping"
        update.effective_user = MagicMock()
        update.effective_user.id = 9
        inc = incoming_from_update(update)
        self.assertIsNotNone(inc)
        assert inc is not None
        self.assertEqual(inc.text, "ping")
        self.assertEqual(inc.user_id, 9)

    def test_incoming_from_update_rejects_no_text(self) -> None:
        update = MagicMock()
        update.message = MagicMock()
        update.message.text = None
        self.assertIsNone(incoming_from_update(update))

    def test_agent_chat_request_dumps(self) -> None:
        self.assertEqual(
            AgentChatRequest(message="hi").model_dump(),
            {"message": "hi", "history": []},
        )

    def test_outcoming_message_model(self) -> None:
        m = OutcomingMessage(text="  x  ")
        self.assertEqual(m.text, "  x  ")


class TestHttpSend(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        get_settings.cache_clear()

    def tearDown(self) -> None:
        get_settings.cache_clear()
        import core.bot as bot_mod

        bot_mod._tg_app = None  # type: ignore[misc]

    @mock.patch.dict(
        os.environ,
        {**_std_env(), "TELEGRAM_BOT_TOKEN": ""},
        clear=True,
    )
    async def test_send_stub(self) -> None:
        from core import bot

        req = mock.AsyncMock()
        req.json = AsyncMock(return_value={"text": "  hello  "})
        res = await bot._http_send(req)  # type: ignore[misc]
        self.assertEqual(res.status, 200)
        body = json.loads(res.body)
        self.assertTrue(body.get("ok"))
        self.assertTrue(body.get("stub"))

    @mock.patch.dict(os.environ, _std_env(), clear=True)
    async def test_send_invalid_payload(self) -> None:
        from core import bot

        req = mock.AsyncMock()
        req.json = AsyncMock(return_value={"nope": 1})
        res = await bot._http_send(req)  # type: ignore[misc]
        self.assertEqual(res.status, 400)

    @mock.patch.dict(
        os.environ,
        {**_std_env(), "TELEGRAM_BOT_TOKEN": ""},
        clear=True,
    )
    async def test_send_rejects_empty_text(self) -> None:
        from core import bot

        req = mock.AsyncMock()
        req.json = AsyncMock(return_value={"text": "   "})
        res = await bot._http_send(req)  # type: ignore[misc]
        self.assertEqual(res.status, 400)


class TestBridge(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        get_settings.cache_clear()

    def tearDown(self) -> None:
        get_settings.cache_clear()

    @mock.patch.dict(os.environ, _std_env(), clear=True)
    async def test_call_agent_returns_text(self) -> None:
        from core.bridge import call_agent

        settings = get_settings()

        mock_resp = MagicMock()
        mock_resp.text = "task created: #42"
        mock_resp.raise_for_status = MagicMock()

        with patch("core.bridge.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            result = await call_agent(settings, "hello")

        self.assertEqual(result, "task created: #42")

    @mock.patch.dict(os.environ, _std_env(), clear=True)
    async def test_call_agent_raises_agent_error_on_http_error(self) -> None:
        import httpx
        from core.bridge import AgentError, call_agent

        settings = get_settings()

        with patch("core.bridge.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_resp = MagicMock()
            mock_resp.status_code = 500
            mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
                "err", request=MagicMock(), response=mock_resp
            )
            mock_client.post = AsyncMock(return_value=mock_resp)
            mock_client_cls.return_value = mock_client

            with self.assertRaises(AgentError):
                await call_agent(settings, "hello")

    @mock.patch.dict(os.environ, _std_env(), clear=True)
    async def test_call_agent_raises_agent_error_on_connection_error(self) -> None:
        import httpx
        from core.bridge import AgentError, call_agent

        settings = get_settings()

        with patch("core.bridge.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(
                side_effect=httpx.ConnectError("refused", request=MagicMock())
            )
            mock_client_cls.return_value = mock_client

            with self.assertRaises(AgentError):
                await call_agent(settings, "hello")


class TestFormatter(unittest.TestCase):
    def test_clean_text_passes_through(self) -> None:
        from core.formatter import format_reply

        self.assertEqual(format_reply("Task #42 created."), "Task #42 created.")

    def test_strips_whitespace(self) -> None:
        from core.formatter import format_reply

        self.assertEqual(format_reply("  hello  "), "hello")

    def test_empty_returns_fallback(self) -> None:
        from core.formatter import format_reply

        result = format_reply("")
        self.assertIn("empty response", result)

    def test_whitespace_only_returns_fallback(self) -> None:
        from core.formatter import format_reply

        result = format_reply("   ")
        self.assertIn("empty response", result)

    def test_error_sentinel_returns_snag(self) -> None:
        from core.formatter import _SNAG_MSG, format_reply

        for sentinel in (
            "[Error: ValueError: something]",
            "[CLI error: timeout]",
            "[CLI timeout: 120s]",
            "[CLI: empty response]",
            "[No LLM provider configured. Set ANTHROPIC_API_KEY]",
            "[CLAWVIS:AUTH]",
            "[CLAWVIS:HTTP:503]",
        ):
            with self.subTest(sentinel=sentinel):
                result = format_reply(sentinel)
                self.assertEqual(result, _SNAG_MSG)

    def test_truncates_at_4096(self) -> None:
        from core.formatter import format_reply

        long_text = "x" * 5000
        result = format_reply(long_text)
        self.assertEqual(len(result), 4096)

    def test_text_at_exactly_4096_not_truncated(self) -> None:
        from core.formatter import format_reply

        text = "y" * 4096
        self.assertEqual(format_reply(text), text)


class TestRouter(unittest.TestCase):
    def test_tasks_command_returns_enriched_prompt(self) -> None:
        from core.router import enrich

        result = enrich("tasks", "create Fix login bug")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertIn("Fix login bug", result)
        self.assertIn("Kanban", result)

    def test_projects_command_returns_enriched_prompt(self) -> None:
        from core.router import enrich

        result = enrich("projects", "list")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertIn("list", result)
        self.assertIn("Kanban", result)

    def test_status_command_ignores_args(self) -> None:
        from core.router import enrich

        result = enrich("status", "")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertIn("/status", result)

    def test_unknown_command_returns_none(self) -> None:
        from core.router import enrich

        self.assertIsNone(enrich("foobar", "anything"))

    def test_empty_args_handled_gracefully(self) -> None:
        from core.router import enrich

        result = enrich("tasks", "")
        self.assertIsNotNone(result)
        assert result is not None
        self.assertIn("Kanban", result)

    def test_tasks_with_no_args_still_returns_prompt(self) -> None:
        from core.router import enrich

        result = enrich("tasks", "   ")
        self.assertIsNotNone(result)


if __name__ == "__main__":
    unittest.main()
