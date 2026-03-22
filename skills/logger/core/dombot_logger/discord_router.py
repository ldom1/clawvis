import discord
import json
from discord.ext import commands
from loguru import logger
from pathlib import Path


class DiscordLoggerBot(commands.Bot):
    def __init__(self, token: str, channel_id: int, command_prefix: str = "!"):
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix=command_prefix, intents=intents)
        self._token = token
        self._channel_id = channel_id
        self._once_message: str | None = None
        self._setup_channels_guild_id: int | None = None
        self._setup_channels_names: list[str] = []
        self._setup_channels_store_path: Path | None = None

    async def setup_hook(self) -> None:
        logger.info("Registering commands")
        self.add_command(self.coucou)
        self.add_command(self.setup_server)
        self.add_command(self.create_private)

    async def on_ready(self) -> None:
        logger.info("No shard used. Connected to Gateway.")
        if self._setup_channels_guild_id is not None:
            await self._run_setup_channels()
            await self.close()
            return
        channel = self.get_channel(self._channel_id)
        if not channel:
            logger.warning("Channel not found for id {}", self._channel_id)
            return
        if self._once_message is not None:
            logger.info("Sending once message then closing")
            await channel.send(self._once_message)
            await self.close()
            return
        logger.info("Sending startup message")
        await channel.send("Le bot est maintenant en ligne !")

    @commands.command()
    async def coucou(self, ctx: commands.Context) -> None:
        logger.info("Command coucou called by {}", ctx.author)
        await ctx.send(f"Salut {ctx.author.mention} !")

    @commands.command()
    async def setup_server(self, ctx: commands.Context) -> None:
        logger.info("Command setup_server called in guild {}", ctx.guild.id if ctx.guild else "none")
        new_channel = await self.create_text_channel(ctx.guild, "bot-logs")
        await new_channel.send(f"Hello! I created this channel. My ID is {new_channel.id}")
        await ctx.send(f"Done! Created {new_channel.mention}")

    @commands.command()
    async def create_private(self, ctx: commands.Context, channel_name: str) -> None:
        logger.info("Command create_private called with channel_name={}", channel_name)
        channel = await self.create_private_channel(ctx.guild, channel_name)
        await channel.send("This is a private channel only I can see (and admins)!")

    def run_bot(self) -> None:
        logger.info("Starting bot (persistent)")
        self.run(self._token)

    def run_once(self, message: str = "Test integration OK") -> None:
        logger.info("Starting bot (once) with message len={}", len(message))
        self._once_message = message
        self.run(self._token)

    def run_setup_channels(
        self, guild_id: int, channel_names: list[str], store_path: Path | None = None
    ) -> None:
        logger.info("Starting bot (setup channels) guild_id={} channels={}", guild_id, channel_names)
        self._setup_channels_guild_id = guild_id
        self._setup_channels_names = channel_names
        self._setup_channels_store_path = store_path
        self.run(self._token)

    async def create_text_channel(self, guild: discord.Guild, channel_name: str) -> discord.TextChannel:
        logger.info("Creating text channel {}", channel_name)
        return await guild.create_text_channel(channel_name)

    async def create_private_channel(
        self, guild: discord.Guild, channel_name: str
    ) -> discord.TextChannel:
        logger.info("Creating private channel {}", channel_name)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            guild.me: discord.PermissionOverwrite(read_messages=True),
        }
        return await guild.create_text_channel(channel_name, overwrites=overwrites)

    def find_text_channel_by_name(
        self, guild: discord.Guild, channel_name: str
    ) -> discord.TextChannel | None:
        logger.info("Searching channel by name {}", channel_name)
        return discord.utils.get(guild.text_channels, name=channel_name)

    async def _run_setup_channels(self) -> None:
        guild = self.get_guild(self._setup_channels_guild_id or 0)
        if guild is None:
            logger.error("Guild not found for id {}", self._setup_channels_guild_id)
            return
        created_or_found: dict[str, str] = {}
        for name in self._setup_channels_names:
            existing = self.find_text_channel_by_name(guild, name)
            if existing:
                logger.info("Channel already exists: {}", name)
                created_or_found[name] = str(existing.id)
                continue
            channel = await self.create_text_channel(guild, name)
            await channel.send(f"Channel created by bot setup: {name}")
            logger.info("Channel created: {} ({})", name, channel.id)
            created_or_found[name] = str(channel.id)
        self._write_channel_store(guild.id, created_or_found)

    def _write_channel_store(self, guild_id: int, channels: dict[str, str]) -> None:
        if not channels:
            return
        path = self._setup_channels_store_path
        if path is None:
            return
        normalized = {k.strip().lower().replace("-", "_"): v for k, v in channels.items() if k and v}
        payload = {
            "guild_id": str(guild_id),
            "channels": normalized,
        }
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            logger.info("Channel store updated: {}", path)
        except OSError as exc:
            logger.error("Failed to write channel store {}: {}", path, exc)
