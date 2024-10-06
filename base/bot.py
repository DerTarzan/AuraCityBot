import os
import asyncio

import discord

from base.database import AuraCityDatabase
from base.logger import AuraCityLogger, AuraCityLoggingUtils, CrashReportHandler
from base.config import AuraCityBotConfig
from base.utils.utilities import AuraCityUtils

# Verwende ein Emoji in den Logger-Nachrichten
logger = AuraCityLogger("AuraCityBot").get_logger()

class AuraCityBot(discord.Bot):
    PRESENCE_UPDATE_INTERVAL = 120

    def __init__(self):
        self.crash_report_handler = CrashReportHandler()
        self.config = AuraCityBotConfig()
        self.utils = AuraCityUtils()
        self.database = AuraCityDatabase()
        self.logger_utils = AuraCityLoggingUtils()
        super().__init__(intents=discord.Intents.all(), debug_guilds=[int(self.config.GUILD_ID_ACSD), int(self.config.GUILD_ID_AC_LOGS)])

    def create_coroutine_task(self, *coros) -> None:
        """Creates and schedules coroutine tasks."""
        for coro in coros:
            if asyncio.iscoroutine(coro):  # Überprüfe, ob es wirklich eine Coroutine ist
                logger.info(f" - ⚙️ Creating task for {coro.__name__}...")
                self.loop.create_task(coro)
            else:
                logger.error(f"❌ Invalid task: {coro} is not a coroutine.")

    def load_cogs(self, directory: str, is_root: bool = True) -> None:
        """Loads all cogs from the specified directory."""
        if is_root:
            logger.info("📦 Loading Cogs...")

        for filename in os.listdir(directory):
            if os.path.isdir(f'{directory}/{filename}'):
                self.load_cogs(f'{directory}/{filename}', is_root=False)
            elif filename.endswith('.py'):
                try:
                    self.load_extension(f'{directory.replace("/", ".")}.{filename[:-3]}')
                    logger.info(f'- ✅ Loaded Cog: {directory}/{filename}')
                except Exception as e:
                    logger.error(f'❌ Failed to load cog {filename}: {e}')
        if is_root:
            logger.info("🎉 All Cogs Loaded Successfully.")

    async def on_ready(self) -> None:
        logger.info("=" * 50)
        logger.info(f"🤖 Bot Name      : {self.user.name}")
        logger.info(f"🆔 Bot ID        : {self.user.id}")
        logger.info(f"🏓 Latency       : {round(self.latency * 1000)} ms")
        logger.info("=" * 50)

        logger.info(f"Connected to {len(self.guilds)} guild(s):")
        logger.info("-" * 50)

        for guild in self.guilds:
            logger.info(f"🏰 Guild Name    : {guild.name}")
            logger.info(f"🆔 Guild ID      : {guild.id}")
            logger.info(f"👥 Member Count  : {guild.member_count}")

            if guild.owner is not None:
                logger.info(f"👑 Owner         : {guild.owner.name}#{guild.owner.discriminator}, ID: {guild.owner.id}")

            logger.info("-" * 50)  # Clearer separation between guilds

        if hasattr(self, "debug_guilds") and self.debug_guilds:
            logger.info("Debug Guilds:")
            for debug_guild in self.debug_guilds:
                logger.info(f" - 🐞 Debug Guild ID: {debug_guild}")
            logger.info("=" * 50)

        logger.info("🔧 Creating presence update task...")
        self.create_coroutine_task(
            self.presence(),
            self.utils.AuraCityUtilities.monitor_server_and_download(),
            self.database.create_database(),
            self.database.backup_database(),
            self.database.schedule_backup(),
            self.logger_utils.schedule_log_backup()
        )
        self.loop.create_task(self.utils.AuraCityUtilities.handle_channel_content(self))

        logger.info("🚀 All tasks created successfully.")
        logger.info("=" * 50)

    async def presence(self) -> None:
        """Updates the bot's presence based on online players."""
        while True:
            players_online = await self.utils.AuraCityUtilities.players_online()
            await self.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching,
                    name=players_online
                )
            )
            await asyncio.sleep(self.PRESENCE_UPDATE_INTERVAL)