import discord
from discord.ext import commands
from discord.commands import slash_command, default_permissions

from base.database import AuraCityDatabase
from base.logger import CrashReportHandler

class Mod(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.crash_report_handler = CrashReportHandler()
        self.database = AuraCityDatabase()
        self.bot = bot

    @slash_command(name="clear", description="/clear <amount> - Löscht eine bestimmte Anzahl von Nachrichten.")
    async def clear(self, ctx: discord.ApplicationContext, amount: int):
        await ctx.channel.purge(limit=amount + 1, check=lambda m: not m.pinned)
        await ctx.respond(f"Successfully cleared {amount} messages.", delete_after=5)

    @slash_command(name="backup_database", description="Erstellt ein Backup der Datenbank.")
    @default_permissions(administrator=True)
    async def backup_database(self, ctx: discord.ApplicationContext):
        await self.database.backup_database()
        await ctx.respond("Backup created successfully.")

    @backup_database.error
    async def on_backup_database_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You do not have the required permissions to use this command.")
        else:
            await self.crash_report_handler.save_error(error)
            await ctx.respond(f"An error occurred. Please contact the ")

    @clear.error
    async def on_application_command_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("You do not have the required permissions to use this command.")
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.respond("Please provide the amount of messages you would like to clear.")
        else:
            await self.crash_report_handler.save_error(error)
            await ctx.respond(f"Es ist ein Fehler aufgetreten. Bitte kontaktiere den ")

def setup(bot: discord.Bot):
    bot.add_cog(Mod(bot))