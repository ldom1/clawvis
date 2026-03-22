"""Tests for dombot_logger.discord_router — Discord bot wrapper."""
import asyncio
from dombot_logger.discord_router import DiscordLoggerBot


class TestDiscordLoggerBot:
    def test_initializes_with_token_and_channel(self):
        bot = DiscordLoggerBot("TOKEN", 1234567890)
        assert bot._token == "TOKEN"
        assert bot._channel_id == 1234567890
        assert bot.command_prefix == "!"

    def test_intents_enable_message_content(self):
        bot = DiscordLoggerBot("TOKEN", 1)
        assert bot.intents.message_content is True


def test_on_ready_sends_message(monkeypatch):
    sent = {}

    class DummyChannel:
        async def send(self, msg):
            sent["msg"] = msg

    bot = DiscordLoggerBot("TOKEN", 42)
    monkeypatch.setattr(bot, "get_channel", lambda *_: DummyChannel())

    asyncio.run(bot.on_ready())  # type: ignore[func-returns-value]
    assert "Le bot est maintenant en ligne" in sent["msg"]


def test_create_text_channel():
    class DummyGuild:
        async def create_text_channel(self, name, **kwargs):
            return type("C", (), {"name": name, "kwargs": kwargs})()

    bot = DiscordLoggerBot("TOKEN", 1)
    ch = asyncio.run(bot.create_text_channel(DummyGuild(), "bot-logs"))
    assert ch.name == "bot-logs"
    assert ch.kwargs == {}


def test_create_private_channel():
    class DummyGuild:
        default_role = object()
        me = object()

        async def create_text_channel(self, name, **kwargs):
            return type("C", (), {"name": name, "kwargs": kwargs})()

    bot = DiscordLoggerBot("TOKEN", 1)
    ch = asyncio.run(bot.create_private_channel(DummyGuild(), "secret"))
    assert ch.name == "secret"
    assert "overwrites" in ch.kwargs
    assert len(ch.kwargs["overwrites"]) == 2


def test_find_text_channel_by_name():
    ch1 = type("C", (), {"name": "general"})()
    ch2 = type("C", (), {"name": "bot-logs"})()
    guild = type("G", (), {"text_channels": [ch1, ch2]})()
    bot = DiscordLoggerBot("TOKEN", 1)
    found = bot.find_text_channel_by_name(guild, "bot-logs")
    missing = bot.find_text_channel_by_name(guild, "unknown")
    assert found is ch2
    assert missing is None
