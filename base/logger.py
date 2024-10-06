import os
import shutil
import asyncio
import logging
import traceback
from typing import Dict
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler

import aiofiles


class AuraCityLoggerConfig:
    def __init__(self):
        self.log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache', 'logs')
        self.log_backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', 'backups', 'logs_backup')
        self.error_log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cache', 'crash_report')
        self.log_backup_count = 5  # Number of backup files for logs
        self.max_log_size = 50 * 1024 * 1024  # Max log file size in bytes (50MB)

class AuraCityLogger(AuraCityLoggerConfig):
    _loggers: Dict[str, logging.Logger] = {}

    def __init__(self, logger_name: str, log_level: int = logging.DEBUG, create_file_handler: bool = True):
        super().__init__()

        if logger_name in self._loggers:
            self.logger = self._loggers[logger_name]
        else:
            self.logger = logging.getLogger(logger_name)
            self.logger.setLevel(log_level)
            formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

            os.makedirs(self.log_path, exist_ok=True)

            if create_file_handler:
                file_handler = RotatingFileHandler(
                    os.path.join(self.log_path, f"{logger_name}.log"),
                    maxBytes=self.max_log_size,
                    backupCount=self.log_backup_count,
                    encoding="utf-8"
                )
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

            root_handler = RotatingFileHandler(
                os.path.join(self.log_path, f"root.log"),
                maxBytes=self.max_log_size,
                backupCount=self.log_backup_count,
                encoding="utf-8"
            )
            root_handler.setLevel(log_level)
            root_handler.setFormatter(formatter)
            self.logger.addHandler(root_handler)

            console_handler = logging.StreamHandler()
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)

            self._loggers[logger_name] = self.logger

    def get_logger(self) -> logging.Logger:
        return self.logger

class AuraCityLoggingUtils(AuraCityLoggerConfig):
    def __init__(self):
        super().__init__()
        self.logger = AuraCityLogger("AuraCityLogUtils").get_logger()

    async def backup_logs(self):
        """Backup the log files to the backup directory."""
        try:
            # Ensure the backup directory exists
            os.makedirs(self.log_backup_path, exist_ok=True)

            # Get a timestamp for the backup folder
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
            backup_dir = os.path.join(self.log_backup_path, f"backup_{timestamp}")

            # Copy all log files to the backup directory
            shutil.copytree(self.log_path, backup_dir)
            self.logger.info(f"Logs successfully backed up to {backup_dir}")

            # Remove old backups if they exceed the backup count limit
            self._clean_old_backups()

        except Exception as e:
            self.logger.error(f"Failed to backup logs: {e}")

    def _clean_old_backups(self):
        """Remove old backups exceeding the log_backup_count limit."""
        try:
            backups = sorted(os.listdir(self.log_backup_path))
            if len(backups) > self.log_backup_count:
                for old_backup in backups[:-self.log_backup_count]:
                    old_backup_path = os.path.join(self.log_backup_path, old_backup)
                    shutil.rmtree(old_backup_path)
                    self.logger.info(f"Old backup removed: {old_backup_path}")
        except Exception as e:
            self.logger.error(f"Failed to clean old backups: {e}")

    async def schedule_log_backup(self):
        """Schedules the log backup every midnight."""
        while True:
            now = datetime.now()
            # Berechne die Zeit bis Mitternacht
            midnight = datetime.combine(now.date() + timedelta(days=1), datetime.min.time())
            seconds_until_midnight = (midnight - now).total_seconds()

            # Berechnung der verbleibenden Zeit
            remaining_time = timedelta(seconds=seconds_until_midnight)
            days = remaining_time.days
            hours, remainder = divmod(remaining_time.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            # Log die verbleibende Zeit bis zur nächsten Sicherung
            time_parts = []
            if days > 0:
                time_parts.append(f"{days} Tag{'e' if days > 1 else ''}")
            if hours > 0:
                time_parts.append(f"{hours} Stunde{'n' if hours > 1 else ''}")
            if minutes > 0:
                time_parts.append(f"{minutes} Minute{'n' if minutes > 1 else ''}")
            if seconds > 0 or not time_parts:
                time_parts.append(f"{seconds} Sekunde{'n' if seconds > 1 else ''}")

            time_until_backup = ", ".join(time_parts)
            self.logger.debug(f"⏳ Waiting for next log backup in: {time_until_backup}")

            # Warte bis Mitternacht
            await asyncio.sleep(seconds_until_midnight)

            # Führe das Log-Backup durch
            await self.backup_logs()


class CrashReportHandler(AuraCityLoggerConfig):
    def __init__(self):
        super().__init__()
        self.log_dir = self.error_log_path
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)  # Verzeichnis erstellen, falls nicht vorhanden

    async def save_error(self, error: Exception, context: str = "") -> None:
        # Erstelle den Grund, was passiert ist, basierend auf dem Fehlernamen und Kontext
        what_happened = f"{error.__class__.__name__}_{context}".replace(" ", "_").lower()
        log_filename = await self._get_unique_filename(what_happened)

        # Sammle die vollständigen Fehlerinformationen
        error_details = "".join(traceback.format_exception(type(error), error, error.__traceback__))

        # Erstelle Crash-Report-Inhalt
        log_content = (
            f"Timestamp: {datetime.now()}\n"
            f"Error Type: {type(error).__name__}\n"
            f"Context: {context}\n"
            f"Error Details:\n{error_details}"
        )

        # Asynchron schreiben mit aiofiles
        async with aiofiles.open(log_filename, 'w') as log_file:
            await log_file.write(log_content)

    async def _get_unique_filename(self, base_name: str) -> str:
        """Erstellt einen einzigartigen Dateinamen basierend auf dem Fehlerereignis."""
        index = 0
        while True:
            if index == 0:
                log_filename = f"{self.log_dir}/crash_log_{base_name}.log"
            else:
                log_filename = f"{self.log_dir}/crash_log_{base_name}_{index:02}.log"

            if not os.path.exists(log_filename):
                break  # Datei existiert nicht, also diesen Namen verwenden
            index += 1

        return log_filename