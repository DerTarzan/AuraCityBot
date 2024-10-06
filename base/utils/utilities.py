import os
import json
import zipfile
from collections import defaultdict, deque

import aiohttp
import asyncio
import discord
import aiofiles
from base.logger import AuraCityLogger
from base.config import AuraCityBotConfig
from datetime import datetime, timedelta

class AuraCityUtilities:
    SLEEP_INTERVAL_PLAYERS = 300  # 5 Minuten in Sekunden
    SLEEP_INTERVAL_OTHERS = 86400   # 24 Stunden in Sekunden
    CHECK_INTERVAL = 5  # Intervall in Sekunden

    def __init__(self):
        self.config = AuraCityBotConfig()
        self.logger = AuraCityLogger("AuraCityBot-Utilities").get_logger()
        self.session = None  # Initialisiere die Session als None
        self.last_download_info = None  # Zeitpunkt des letzten Downloads für Info
        self.last_download_dynamic = None  # Zeitpunkt des letzten Downloads für Dynamic
        self.user_message_count = defaultdict(list)  # Benutzer-ID zu einer Liste von Nachrichtenzeitstempeln

    async def async_init(self) -> None:
        """Initialisiere die HTTP-Client-Session."""
        if self.session is None:
            try:
                self.session = aiohttp.ClientSession()  # Initialisiere die Session im asynchronen Kontext
                self.logger.debug("HTTP ClientSession initialisiert.")
            except Exception as e:
                self.logger.error(f"Fehler beim Initialisieren der Session: {e}")
                if self.session is not None:
                    await self.session.close()
                    self.session = None

    async def close(self) -> None:
        """Schließe die HTTP-Client-Session."""
        if self.session is not None:
            await self.session.close()  # Schließe die Session, wenn sie nicht mehr benötigt wird
            self.session = None
            self.logger.debug("HTTP ClientSession geschlossen.")

    async def download_if_online(self) -> None:
        """Überprüfe, ob der Server online ist und lade JSON-Daten von vordefinierten URLs herunter."""
        if self.session is None:
            await self.async_init()  # Stelle sicher, dass die Session initialisiert ist

        if await self.server_status():
            await self.download_player_count()  # Lade Spieleranzahl alle 5 Minuten
            await self.download_info_and_dynamic()  # Lade info und Dynamic alle 24 Stunden
        else:
            self.logger.warning("Server ist offline. Herunterladen übersprungen.")

    async def download_player_count(self) -> None:
        """Lade die Spieleranzahl herunter und speichere sie in einer Datei."""
        await self._download_and_save(self.config.FIVEM_PLAYER_URL, "fivem_players.json")

    async def download_info_and_dynamic(self) -> None:
        """Lade info und Dynamic herunter, falls die Zeit dafür reif ist."""
        now = datetime.now()

        # Überprüfe, ob die Downloads für info und Dynamic durchgeführt werden sollten
        if self.last_download_info is None or now >= self.last_download_info + timedelta(seconds=self.SLEEP_INTERVAL_OTHERS):
            await self._download_and_save(self.config.FIVEM_INFO_URL, "fivem_info.json")
            self.last_download_info = now  # Aktualisiere den Zeitpunkt des letzten Downloads

        if self.last_download_dynamic is None or now >= self.last_download_dynamic + timedelta(seconds=self.SLEEP_INTERVAL_OTHERS):
            await self._download_and_save(self.config.FIVEM_DYNAMIC_URL, "fivem_dynamic.json")
            self.last_download_dynamic = now  # Aktualisiere den Zeitpunkt des letzten Downloads

    async def _download_and_save(self, url: str, filename: str) -> None:
        """Hilfsmethode zum Herunterladen von JSON-Daten von der angegebenen URL und zum Speichern in einer Datei."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    text = await response.text()
                    try:
                        data = json.loads(text)
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Fehler beim Dekodieren von JSON: {e}. Inhalt: {text[:100]}...")  # Zeige die ersten 100 Zeichen an
                        return  # Beende die Funktion, wenn das Dekodieren fehlschlägt

                    # Daten speichern
                    os.makedirs("base/cache", exist_ok=True)  # Stelle sicher, dass das Verzeichnis existiert
                    file_path = os.path.join("base/cache", filename)
                    async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
                        await f.write(json.dumps(data, indent=4))
                    self.logger.debug(f"{filename} erfolgreich heruntergeladen und gespeichert. [{response.status}]")
                else:
                    self.logger.error(f"Fehler beim Herunterladen von Daten von {url}: {response.status}")
        except aiohttp.ClientError as e:
            self.logger.error(f"Fehler beim Herunterladen von Daten von {url}: {e}")

    async def server_status(self) -> bool:
        """Überprüfe den Status des Servers."""
        if self.session is None:
            await self.async_init()  # Stelle sicher, dass die Session initialisiert ist

        try:
            async with self.session.get(self.config.FIVEM_SERVER_URL) as response:
                if response.status == 200:
                    return True
                else:
                    self.logger.error(f"Serverstatus ist nicht 200: {response.status}")
                    return False
        except aiohttp.ClientError:
            return False

    async def get_player_count(self) -> int:
        """Hole die Anzahl der online Spieler."""
        if not await self.server_status():
            return 0  # Gebe 0 zurück, wenn der Server offline ist

        try:
            async with self.session.get(self.config.FIVEM_PLAYER_URL) as response:
                if response.status == 200:
                    text = await response.text()
                    try:
                        data = json.loads(text)
                        if isinstance(data, list):
                            return len(data)  # Gebe die Anzahl der Spieler zurück
                        else:
                            self.logger.error("Unerwartetes Datenformat erhalten.")
                            return 0
                    except json.JSONDecodeError as e:
                        self.logger.error(f"Fehler beim Dekodieren von JSON: {e}")
                        return 0  # Gebe 0 zurück im Fehlerfall
                else:
                    self.logger.error(f"Fehler beim Abrufen der Spieldaten: {response.status}")
                    return 0  # Gebe 0 zurück im Statusfehlerfall
        except aiohttp.ClientError as e:
            self.logger.error(f"Fehler beim Abrufen der Spieleranzahl: {e}")
            return 0  # Gebe 0 zurück bei Ausnahme

    async def players_online(self) -> str:
        count = await self.get_player_count()
        if count == 0:
            if await self.server_status():
                return "Keine Spieler online."
            return "Server ist offline."
        return f"{count} Spieler online."


    async def monitor_server_and_download(self):
        """Überwache den Serverstatus und versuche, Daten herunterzuladen, wenn er online ist."""
        while True:
            await self.download_if_online()
            await asyncio.sleep(self.SLEEP_INTERVAL_PLAYERS)  # Verwende die Konstante für Schlafintervall der Spieler

    @staticmethod
    def file_to_zip(file_path: str) -> str:
        """Zippe eine Datei und gebe den Pfad zur Zip-Datei zurück."""
        get_file_name = os.path.basename(file_path)
        zip_file_name = f"{get_file_name}.zip"

        try:
            with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(file_path, get_file_name)
            return zip_file_name
        except Exception as e:
            AuraCityLogger("AuraCityBot-Utilities").get_logger().error(f"Fehler beim Zipping der Datei: {e}")
            return ""

    async def ban_bot(self, user: discord.Member) -> None:
        """Bans the bot from the server."""
        await user.ban(reason="Bot wurde aus dem Server verbannt.")
        self.logger.debug(f"Bot {user} wurde aus dem Server verbannt.")

    async def send_dm(self, user: discord.Member, content: str) -> None:
        """Send a direct message to the user."""
        try:
            await user.send(content, delete_after=10)
        except discord.Forbidden:
            self.logger.warning(f"Could not send a message to {user} (likely due to DM settings).")

    async def handle_spam(self, message: discord.Message) -> None:
        """Handle spam detection and take action."""
        user = message.author
        user_id = user.id

        if user_id == message.guild.owner_id:
            self.logger.debug(f"Server owner {user} ID: {user_id} cannot be kicked.")#
            del self.user_message_count[user_id]  # Clear their message count after kicking
            return

        await user.kick(reason="Spam detected: More than 5 messages in a short time.")
        self.logger.debug(f"User {user} was kicked for spamming.")

        await self.send_dm(user, "Du wurdest wegen Spamming gekickt. Wenn du dich beruhigt hast, komm auf den Server zurück: Link")

        if user_id in self.user_message_count:
            del self.user_message_count[user_id]  # Clear their message count after kicking
            self.logger.debug(f"User {user} message count cleared after kicking.")

    async def check_spam(self, message: discord.Message) -> bool:
        """Überprüfe, ob der Benutzer in den letzten 60 Sekunden zu viele Nachrichten gesendet hat."""
        user_id = message.author.id
        current_time = message.created_at

        # Aktuelle Zeit der Nachricht zur Liste hinzufügen
        self.user_message_count[user_id].append(current_time)

        # Entferne Nachrichten, die älter als 60 Sekunden sind
        self.user_message_count[user_id] = [
            msg_time for msg_time in self.user_message_count[user_id]
            if (current_time - msg_time).total_seconds() < 60
        ]

        message_count = len(self.user_message_count[user_id])

        # Wenn der Benutzer mehr als 5 Nachrichten in 60 Sekunden gesendet hat, gilt dies als Spam
        if message_count > 5:
            await self.handle_spam(message)
            return True

        return False

    async def handle_status_lspd(self, bot: discord.Bot, count: int):
        """Handle the status of the LSPD channel."""
        guild = bot.get_guild(int(self.config.GUILD_ID_ACSD))

        if guild is None:
            self.logger.error("Guild not found.")
            return

        channel = guild.get_channel(int(self.config.LSPD_COUNTER_CHANNEL_ID))

        if channel is None:
            self.logger.error("Channel not found.")
            return

        name = f"🚓 {count}"
        try:
            await channel.edit(name=name)
        except discord.HTTPException as e:
            self.logger.error(f"Error editing channel: {e}")

    async def handle_status_lsmd(self, bot: discord.Bot, count: int):
        """Handle the status of the LSMD channel."""
        guild = bot.get_guild(int(self.config.GUILD_ID_ACSD))

        if guild is None:
            self.logger.error("Guild not found.")
            return

        channel = guild.get_channel(int(self.config.LSMD_COUNTER_CHANNEL_ID))

        if channel is None:
            self.logger.error("Channel not found.")
            return

        name = f"🚑 {count}"
        try:
            await channel.edit(name=name)
        except discord.HTTPException as e:
            self.logger.error(f"Error editing channel: {e}")


    async def handle_channel_content(self, bot: discord.Bot):
        guild = bot.get_guild(int(self.config.GUILD_ID_ACSD))
        if guild is None:
            self.logger.error("Guild not found.")
            return

        # Abrufen der Kanäle
        channels = {
            "rules_channel": guild.get_channel(int(self.config.RULES_CHANNEL_ID)),
            "gesetze_channel": guild.get_channel(int(self.config.GESETZE_CHANNEL_ID)),
            "vorraum_channel": guild.get_channel(int(self.config.VORRAUM_CHANNEL_ID)),
            "rechtsanfrage_lsmd_channel": guild.get_channel(int(self.config.LSMD_RECHTSANFRAGE_CHANNEL_ID)),
            "rechtsanfrage_lspd_channel": guild.get_channel(int(self.config.LSPD_RECHTSANFRAGE_CHANNEL_ID)),
            "funkcodes_channel": guild.get_channel(int(self.config.FUNKCODES_CHANNEL_ID)),
            "lsmd_bescherden_channel": guild.get_channel(int(self.config.LSMD_BESCHWERDE_CHANNEL_ID)),
            "lspd_bescherden_channel": guild.get_channel(int(self.config.LSPD_BESCHWERDE_CHANNEL_ID))
        }

        if any(channel is None for channel in channels.values()):
            self.logger.error("One or more channels not found. Please check the environment variables.")
            return

        # Nachrichten gleichzeitig löschen
        await asyncio.gather(*(channel.purge(limit=30) for channel in channels.values()))

        # Nachrichten gleichzeitig senden
        messages = await asyncio.gather(
            channels["rules_channel"].send("Regeln"),
            channels["gesetze_channel"].send("Gesetze"),
            channels["vorraum_channel"].send("Vorraum für neue Mitglieder"),
            channels["rechtsanfrage_lsmd_channel"].send("Rechtsanfrage LSMD"),
            channels["rechtsanfrage_lspd_channel"].send("Rechtsanfrage LSPD"),
            channels["funkcodes_channel"].send("Funkcodes"),
            channels["lsmd_bescherden_channel"].send("Beschwerden LSMD"),
            channels["lspd_bescherden_channel"].send("Beschwerden LSPD")
        )

        # Nachrichten gleichzeitig pinnen
        await asyncio.gather(*(message.pin() for message in messages))

class AuraCityRateLimitQueue:
    def __init__(self, rate_limit_per_second: int, batch_size: int = 1):
        self.queue: deque[asyncio.Task] = deque()
        self.processing = False
        self.rate_limit_per_second = rate_limit_per_second  # Anzahl der erlaubten Anfragen pro Sekunde
        self.batch_size = batch_size  # Optional: Anzahl der Aufrufe, die in einem Batch verarbeitet werden können

    async def process_queue(self):
        if self.processing:
            return  # Verhindere, dass die Verarbeitung doppelt startet

        self.processing = True
        try:
            while self.queue:
                # Verarbeite die Anfragen in Batches, falls gewünscht
                for _ in range(min(self.batch_size, len(self.queue))):
                    task = self.queue.popleft()
                    await task  # Führe die nächste Aufgabe aus

                # Warte nach jedem Batch, um die Rate-Limits einzuhalten
                await asyncio.sleep(1 / self.rate_limit_per_second)

        finally:
            self.processing = False

    def add_to_queue(self, coroutine: asyncio.Task) -> None:
        """Fügt eine neue Aufgabe zur Warteschlange hinzu"""
        self.queue.append(coroutine)
        asyncio.create_task(self.process_queue())  # Starte die Verarbeitung im Hintergrund

class AuraCityUtils:
    def __init__(self):
        self.rate_limit_queue = AuraCityRateLimitQueue(rate_limit_per_second=1, batch_size=5)
        self.AuraCityUtilities = AuraCityUtilities()
