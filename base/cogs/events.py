import asyncio

import discord
from discord.ext import commands

from base.config import AuraCityBotConfig
from base.database import AuraCityDatabase
from base.logger import CrashReportHandler
from base.utils.utilities import AuraCityUtils


class Events(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.crash_report_handler = CrashReportHandler()
        self.database = AuraCityDatabase()
        self.utils = AuraCityUtils()
        self.config = AuraCityBotConfig()
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        try:
            if member.bot:
                await self.utils.AuraCityUtilities.ban_bot(member)

            welcome_channel = self.bot.get_channel(self.config.WELCOME_CHANNEL_ID)
            logs_join_channel = self.bot.get_channel(self.config.JOIN_LOGS_CHANNEL_ID)

            # Überprüfen, ob der User in der Datenbank ist
            if await self.database.get_user(member.id) is None:
                await self.database.add_user(member.id, member.discriminator)  # User zur Datenbank hinzufügen
                self.queue.add_to_queue(welcome_channel.send(f"Willkommen auf dem Server, {member.mention}!"))
                self.queue.add_to_queue(logs_join_channel.send(f"{member.mention} is joined the server (first time)."))  # Log-Nachricht
            else:
                self.queue.add_to_queue(welcome_channel.send(f"Willkommen zurück, {member.mention}!"))  # Rückkehrer begrüßen
                self.queue.add_to_queue(logs_join_channel.send(f"{member.mention} is joined the server (returning)."))  # Log-Nachricht

        except Exception as e:
            error_channel = self.bot.get_channel(self.config.ERROR_LOGS_CHANNEL_ID)
            await self.crash_report_handler.save_error(e)
            self.queue.add_to_queue(error_channel.send(f"Ein Fehler ist aufgetreten, als {member.mention} dem Server beigetreten ist: {str(e)}"))

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        try:
            channel = self.bot.get_channel(self.config.LEAVE_LOGS_CHANNEL_ID)
            self.queue.add_to_queue(channel.send(f"Has left the server: {member.mention}"))
            await asyncio.sleep(3)

        except Exception as e:
            error_channel = self.bot.get_channel(self.config.ERROR_LOGS_CHANNEL_ID)
            await self.crash_report_handler.save_error(e)
            self.queue.add_to_queue(error_channel.send(
                f"Ein Fehler ist aufgetreten, als {member.mention} den Server verlassen hat: {str(e)}"))


def setup(bot: discord.Bot):
    bot.add_cog(Events(bot))