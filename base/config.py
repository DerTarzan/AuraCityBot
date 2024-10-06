import os

from dotenv import load_dotenv
from functools import lru_cache

class ConfigError(Exception):
    """Custom exception for configuration-related errors."""
    pass

class AuraCityBotConfigHandler:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AuraCityBotConfigHandler, cls).__new__(cls, *args, **kwargs)
            print("Creating new instance of: " + cls.__name__ + " class with id: " + str(id(cls)))
        return cls._instance

    def __init__(self, dev_mode=None):
        self.DEV_MODE = dev_mode  # Setze DEV_MODE standardmäßig auf True
        self.load_dotenvs()

    @staticmethod
    def load_dotenv_file(path):
        """
        Loads a .env file and raises a FileNotFoundError if loading fails.
        """
        if not load_dotenv(path):
            raise FileNotFoundError(f"Fehler beim Laden der Konfigurationsdatei: {path}")

    def load_dotenvs(self):
        """
        Lädt die entsprechende .env-Datei basierend auf dem dev_mode und setzt eine Umgebungsvariable,
        die den aktuellen Modus widerspiegelt (dev_mode=True oder False).
        """
        try:
            if self.DEV_MODE:
                # Dev Mode aktiviert - Lade dev-spezifische Konfigurationen
                # self.load_dotenv_file("base/resources/secrets/AC/server_dev_config.env")
                self.load_dotenv_file("base/resources/secrets/AC_LOG/dev_server_config.env")
                self.load_dotenv_file("base/resources/secrets/AC_SD/dev_server_config.env")
                os.environ["DEV_MODE"] = "True"  # Setze den dev_mode in die Umgebungsvariable
            else:
                # Dev Mode deaktiviert - Lade Production Konfigurationen
                #self.load_dotenv_file("base/resources/secrets/AC/server_config.env")
                self.load_dotenv_file("base/resources/secrets/AC_LOG/server_config.env")
                self.load_dotenv_file("base/resources/secrets/AC_SD/server_config.env")
                os.environ["DEV_MODE"] = "False"  # Setze den dev_mode in die Umgebungsvariable

            self.load_dotenv_file("base/resources/secrets/config.env")
            self.load_dotenv_file("base/resources/secrets/tokens.env")

        except FileNotFoundError as e:
            raise ConfigError(f"Konfigurationsfehler: {str(e)}")

    def is_dev_mode(self):
        """
        Gibt zurück, ob der Dev Mode aktiviert ist, basierend auf der Umgebungsvariable 'DEV_MODE'.
        """
        return self.DEV_MODE


class AuraCityBotConfig(AuraCityBotConfigHandler):
    def __init__(self, dev_mode=True):
        super().__init__(dev_mode)

    @property
    @lru_cache(maxsize=None)
    def TOKEN(self) -> str:
        """Returns the bot token based on the development mode."""
        token_key = "TOKEN_AURACITY_BOT_DEV" if self.is_dev_mode() else "TOKEN_AURACITY_BOT"
        return self._get_env_variable(token_key)

    @property
    @lru_cache(maxsize=None)
    def CLIENT_ID(self) -> str:
        """Returns the client ID."""
        client_id = "CLIENT_ID_AURACITY_BOT_DEV" if self.is_dev_mode() else "CLIENT_ID_AURACITY_BOT"
        return str(self._get_env_variable(client_id))

    @property
    @lru_cache(maxsize=None)
    def GUILD_ID_AC(self) -> int:
        """Returns the Guild ID for AC based on the development mode."""
        guild_id_key = "GUILD_ID_AC_DEV" if self.is_dev_mode() else "GUILD_ID_AC"
        return int(self._get_env_variable(guild_id_key))

    @property
    @lru_cache(maxsize=None)
    def GUILD_ID_ACSD(self) -> int:
        """Returns the Guild ID for ACSD based on the development mode."""
        guild_id_key = "GUILD_ID_ACSD_DEV" if self.is_dev_mode() else "GUILD_ID_ACSD"
        return int(self._get_env_variable(guild_id_key))

    @property
    @lru_cache(maxsize=None)
    def GUILD_ID_AC_LOGS(self) -> int:
        """Returns the Guild ID for AC Logs based on the development mode."""
        guild_id_key = "GUILD_ID_AC_LOGS_DEV" if self.is_dev_mode() else "GUILD_ID_AC_LOGS"
        return int(self._get_env_variable(guild_id_key))


    # Füge die LogChannel IDs hinzu
    @property
    @lru_cache(maxsize=None)
    def ALL_LOGS_CHANNEL_ID(self) -> int:
        return self._get_channel_id("ALL_LOGS")

    @property
    @lru_cache(maxsize=None)
    def JOIN_LOGS_CHANNEL_ID(self) -> int:
        return self._get_channel_id("JOIN_LOGS")

    @property
    @lru_cache(maxsize=None)
    def LEAVE_LOGS_CHANNEL_ID(self) -> int:
        return self._get_channel_id("LEAVE_LOGS")

    @property
    @lru_cache(maxsize=None)
    def ERROR_LOGS_CHANNEL_ID(self) -> int:
        return self._get_channel_id("ERROR_LOGS")

    @property
    @lru_cache(maxsize=None)
    def BACKUP_LOGS_CHANNEL_ID(self) -> int:
        return self._get_channel_id("BACKUP_LOGS")

    @property
    @lru_cache(maxsize=None)
    def FIVEM_SERVER_URL(self) -> str:
        """Returns the FiveM server URL."""
        return self._get_env_variable("FIVEM_SERVER_URL")

    @property
    @lru_cache(maxsize=None)
    def FIVEM_INFO_URL(self) -> str:
        """Returns the FiveM info URL."""
        return self._get_env_variable("FIVEM_INFO_URL")

    @property
    @lru_cache(maxsize=None)
    def FIVEM_PLAYER_URL(self) -> str:
        """Returns the FiveM player URL."""
        return self._get_env_variable("FIVEM_PLAYER_URL")

    @property
    @lru_cache(maxsize=None)
    def FIVEM_DYNAMIC_URL(self) -> str:
        """Returns the FiveM dynamic URL."""
        return self._get_env_variable("FIVEM_DYNAMIC_URL")

    @property
    @lru_cache(maxsize=None)
    def DATABASE_PATH(self) -> str:
        """Returns the database path."""
        return self._get_env_variable("DATABASE_PATH")

    @property
    @lru_cache(maxsize=None)
    def DATABASE_BACKUP_PATH(self) -> str:
        """Returns the database backup path."""
        return self._get_env_variable("DATABASE_BACKUP_PATH")

    @property
    @lru_cache(maxsize=None)
    def DISCORD_BACKUP_PATH(self) -> str:
        """Returns the discord backup path."""
        return self._get_env_variable("DISCORD_BACKUP_PATH")

    @property
    @lru_cache(maxsize=None)
    def DISCORD_BACKUP_TEMP_PATH(self) -> str:
        """Returns the discord backup temp path."""
        return self._get_env_variable("DISCORD_BACKUP_TEMP_PATH")

    # AC Statsfraktionen Channel IDs
    @property
    @lru_cache(maxsize=None)
    def WELCOME_CHANNEL_ID(self):
        return self._get_channel_id("WELCOME_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def SERVER_STATUS_CHANNEL_ID(self):
        return self._get_channel_id("SERVER_STATUS_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def LSPD_COUNTER_CHANNEL_ID(self):
        return self._get_channel_id("LSPD_COUNTER_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def LSMD_COUNTER_CHANNEL_ID(self):
        return self._get_channel_id("LSMD_COUNTER_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def VORRAUM_CHANNEL_ID(self):
        return self._get_channel_id("VORRAUM_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def RULES_CHANNEL_ID(self):
        return self._get_channel_id("RULES_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def GESETZE_CHANNEL_ID(self):
        return self._get_channel_id("GESETZE_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def LSMD_RECHTSANFRAGE_CHANNEL_ID(self):
        return self._get_channel_id("LSMD_RECHTSANFRAGE_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def LSPD_RECHTSANFRAGE_CHANNEL_ID(self):
        return self._get_channel_id("LSPD_RECHTSANFRAGE_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def FUERUNGEN_CHANNEL_ID(self):
        return self._get_channel_id("FUERUNGEN_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def FUNKCODES_CHANNEL_ID(self):
        return self._get_channel_id("FUNKCODES_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def LSPD_BESCHWERDE_CHANNEL_ID(self):
        return self._get_channel_id("LSPD_BESCHWERDE_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def LSPD_ABMELDUNG_CHANNEL_ID(self):
        return self._get_channel_id("LSPD_ABMELDUNG_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def LSPD_BEFOERDERUNG_CHANNEL_ID(self):
        return self._get_channel_id("LSPD_BEFOERDERUNG_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def LSPD_ENTLASSUNG_CHANNEL_ID(self):
        return self._get_channel_id("LSPD_ENTLASSUNGS_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def LSMD_BESCHWERDE_CHANNEL_ID(self):
        return self._get_channel_id("LSMD_BESCHWERDE_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def LSMD_ABMELDUNG_CHANNEL_ID(self):
        return self._get_channel_id("LSMD_ABMELDUNG_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def LSMD_BEFOERDERUNG_CHANNEL_ID(self):
        return self._get_channel_id("LSMD_BEFOERDERUNG_CHANNEL_ID")

    @property
    @lru_cache(maxsize=None)
    def LSMD_ENTLASSUNG_CHANNEL_ID(self):
        return self._get_channel_id("LSMD_ENTLASSUNG_CHANNEL_ID")

    # AC Statsfraktionen Role IDs
    @property
    @lru_cache(maxsize=None)
    def LSPD_FUERUNG_ROLE_ID(self):
        return self._get_role_id("LSPD_FUERUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def LSMD_FUERUNG_ROLE_ID(self):
        return self._get_role_id("LSMD_FUERUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def LSPD_LEITUNG_ROLE_ID(self):
        return self._get_role_id("LSPD_LEITUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def LSMD_LEITUNG_ROLE_ID(self):
        return self._get_role_id("LSMD_LEITUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def LSPD_AUSBILDUNGSLEITUNG_ROLE_ID(self):
        return self._get_role_id("LSPD_AUSBILDUNGSLEITUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def LSPD_STV_AUSBILDUNGSLEITUNG_ROLE_ID(self):
        return self._get_role_id("LSPD_STV_AUSBILDUNGSLEITUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def LSMD_AUSBILDUNGSLEITUNG_ROLE_ID(self):
        return self._get_role_id("LSMD_AUSBILDUNGSLEITUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def LSMD_STV_AUSBILDUNGSLEITUNG_ROLE_ID(self):
        return self._get_role_id("LSMD_STV_AUSBILDUNGSLEITUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def LSPD_BEWERBUNGSLEITUNG_ROLE_ID(self):
        return self._get_role_id("LSPD_BEWERBUNGSLEITUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def LSPD_STV_BEWERBUNGSLEITUNG_ROLE_ID(self):
        return self._get_role_id("LSPD_STV_BEWERBUNGSLEITUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def LSMD_BEWERBUNGSLEITUNG_ROLE_ID(self):
        return self._get_role_id("LSMD_BEWERBUNGSLEITUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def LSMD_STV_BEWERBUNGSLEITUNG_ROLE_ID(self):
        return self._get_role_id("LSMD_STV_BEWERBUNGSLEITUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def SUPERVISOR_LEITUNG_ROLE_ID(self):
        return self._get_role_id("SUPERVISOR_LEITUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def STV_SUPERVISOR_LEITUNG_ROLE_ID(self):
        return self._get_role_id("STV_SUPERVISOR_LEITUNG_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def SUPERVISOR_ROLE_ID(self):
        return self._get_role_id("SUPERVISOR_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def CHIEF_OF_POLICE_ROLE_ID(self):
        return self._get_role_id("CHIEF_OF_POLICE_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def KLINISCHER_DIREKTOR_ROLE_ID(self):
        return self._get_role_id("KLINISCHER_DIREKTOR_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def VORRAUM_LSPD(self):
        return self._get_role_id("VORRAUM_LSPD")

    @property
    @lru_cache(maxsize=None)
    def VORRAUM_LSMD(self):
        return self._get_role_id("VORRAUM_LSMD")

    @property
    @lru_cache(maxsize=None)
    def LSPD_ROLE_ID(self):
        return self._get_role_id("LSPD_ROLE_ID")

    @property
    @lru_cache(maxsize=None)
    def LSMD_ROLE_ID(self):
        return self._get_role_id("LSMD_ROLE_ID")

    # Helper methods to fetch environment variables
    @staticmethod
    def _get_channel_id(key):
        channel_id = os.getenv(key)
        if not channel_id or not channel_id.isdigit():
            raise ConfigError(f"Die Channel-ID für {key} konnte nicht geladen werden")
        return int(channel_id)

    @staticmethod
    def _get_role_id(key):
        role_id = os.getenv(key)
        if not role_id or not role_id.isdigit():
            raise ConfigError(f"Die Rollen-ID für {key} konnte nicht geladen werden")
        return int(role_id)

    @staticmethod
    def _get_env_variable(key: str) -> str:
        """Fetches an environment variable and raises ConfigError if not found."""
        value = os.getenv(key)
        if not value:
            raise ConfigError(f"Die Umgebungsvariable '{key}' konnte nicht geladen werden")
        return value