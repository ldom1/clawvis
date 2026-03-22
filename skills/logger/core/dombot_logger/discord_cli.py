from pathlib import Path

import typer
from dotenv import load_dotenv
from loguru import logger
from pydantic import ValidationError

from dombot_logger.config import get as config_get, get_discord_channel
from dombot_logger.discord_router import DiscordLoggerBot
from dombot_logger.models import DiscordCliCreateChannelsConfig, DiscordCliRunConfig

app = typer.Typer(add_completion=False)


@app.command()
def main(
    once: bool = typer.Option(False, "--once"),
    message: str = typer.Option("Test integration OK", "--message"),
    channel_id: str = typer.Option("", "--channel-id"),
) -> None:
    logger.info("discord-cli start (once={}, channel_override={})", once, bool(channel_id))
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    token = config_get("DISCORD_BOT_TOKEN")
    resolved_channel_id = channel_id or get_discord_channel("general")
    if channel_id and not channel_id.isdigit():
        resolved_channel_id = get_discord_channel(channel_id, channel_id)
    try:
        cfg = DiscordCliRunConfig(
            token=token,
            channel_id=int(resolved_channel_id),
            once=once,
            message=message,
        )
    except (TypeError, ValueError, ValidationError):
        logger.error("Missing/invalid DISCORD_BOT_TOKEN or channel id")
        raise SystemExit(
            "Missing/invalid DISCORD_BOT_TOKEN or channel id (use --channel-id or env/store)"
        ) from None
    logger.info("Using channel id: {}", cfg.channel_id)
    bot = DiscordLoggerBot(cfg.token, cfg.channel_id)
    if cfg.once:
        logger.info("Running once mode")
        bot.run_once(cfg.message)
        return
    logger.info("Running persistent bot mode")
    bot.run_bot()


@app.command("create-channels")
def create_channels(
    guild_id: str = typer.Option("", "--guild-id"),
    channels: str = typer.Option("logs,innovations,projects,ops", "--channels"),
    channel_id: str = typer.Option("", "--channel-id"),
    store_path: str = typer.Option(".local/discord_channels.json", "--store-path"),
) -> None:
    load_dotenv(Path(__file__).resolve().parents[1] / ".env")
    token = config_get("DISCORD_BOT_TOKEN")
    final_guild_id = guild_id or config_get("DISCORD_GUILD_ID")
    resolved_channel_id = channel_id or get_discord_channel("general")
    if channel_id and not channel_id.isdigit():
        resolved_channel_id = get_discord_channel(channel_id, channel_id)
    try:
        cfg = DiscordCliCreateChannelsConfig(
            token=token,
            guild_id=int(final_guild_id),
            channel_id=int(resolved_channel_id),
            channels=channels.split(","),
            store_path=store_path,
        )
    except (TypeError, ValueError, ValidationError):
        raise SystemExit(
            "Missing/invalid DISCORD_BOT_TOKEN, DISCORD_GUILD_ID or channel id"
        ) from None
    resolved_store_path = Path(__file__).resolve().parents[1] / cfg.store_path
    logger.info("Creating channels in guild {}: {}", cfg.guild_id, cfg.channels)
    logger.info("Store file: {}", resolved_store_path)
    bot = DiscordLoggerBot(cfg.token, cfg.channel_id)
    bot.run_setup_channels(cfg.guild_id, cfg.channels, store_path=resolved_store_path)

