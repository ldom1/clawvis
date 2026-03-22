"""Tests for dombot_logger.config — load_env does not override existing vars."""
from unittest.mock import patch

from dombot_logger import config


class TestLoadEnv:
    def test_load_env_calls_dotenv_with_override_false(self):
        """load_dotenv is called with override=False so existing env is not overridden."""
        with patch("dotenv.load_dotenv") as load_dotenv:
            config.load_env()
            assert load_dotenv.called
            for call in load_dotenv.call_args_list:
                assert call.kwargs.get("override") is False

    def test_get_returns_stripped_env(self, monkeypatch):
        monkeypatch.setenv("DOMBOT_DISCORD_ALERTS", "  123456789  ")
        assert config.get("DOMBOT_DISCORD_ALERTS") == "123456789"
        monkeypatch.delenv("DOMBOT_DISCORD_ALERTS", raising=False)

    def test_get_missing_returns_default(self):
        assert config.get("DOMBOT_NONEXISTENT_KEY_XYZ", "default") == "default"


class TestDiscordChannelMap:
    def test_get_discord_channel_by_readable_name(self, monkeypatch):
        monkeypatch.setenv("DISCORD_CHANNEL_ID_GENERAL", "111")
        monkeypatch.setenv("DISCORD_CHANNEL_ID_LOGS", "222")
        assert config.get_discord_channel("general") == "111"
        assert config.get_discord_channel("logs") == "222"

    def test_get_discord_channel_unknown(self):
        assert config.get_discord_channel("unknown", "x") == "x"
