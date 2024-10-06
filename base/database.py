import os
import asyncio

import aiosqlite
from typing import Optional, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from base.logger import AuraCityLogger, CrashReportHandler
from base.config import AuraCityBotConfig


class AuraCityDatabaseConnectionHandler:
    def __init__(self) -> None:
        self.config = AuraCityBotConfig()
        self.crash_report_handler = CrashReportHandler()
        self.conn_database_logger = AuraCityLogger("AuraCityDatabaseConnection").get_logger()
        self.db = self.config.DATABASE_PATH
        self.connection: Optional[aiosqlite.Connection] = None
        self.backup_interval = 86400  # 1 day

    async def create_database(self) -> None:
        await self.create_connection()
        try:
            async with self.connection.cursor() as cursor:
                created_tables = []  # Liste für erstellte Tabellen

                # Definieren der Tabellen
                tables = [
                    ("users", """
                        CREATE TABLE IF NOT EXISTS users (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            discord_id INTEGER UNIQUE NOT NULL,
                            discriminator TEXT NOT NULL
                        )
                    """),
                    ("bans", """
                        CREATE TABLE IF NOT EXISTS bans (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            discord_id INTEGER NOT NULL,
                            reason TEXT NOT NULL,
                            FOREIGN KEY (discord_id) REFERENCES users(discord_id)
                        )
                    """),
                    ("blacklist", """
                        CREATE TABLE IF NOT EXISTS blacklist (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            discord_id INTEGER NOT NULL,
                            reason TEXT NOT NULL,
                            FOREIGN KEY (discord_id) REFERENCES users(discord_id)
                        )
                    
                    """),
                    ("deregistrations", """
                        CREATE TABLE IF NOT EXISTS deregistrations (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            discord_id INTEGER NOT NULL,
                            time_stamp TIMESTAMP NOT NULL,
                            deregistration_count INTEGER NOT NULL,
                            reason TEXT NOT NULL,
                            message TEXT NOT NULL,
                            FOREIGN KEY (discord_id) REFERENCES users(discord_id)
                        )
                    """),
                    ("complaints", """
                        CREATE TABLE IF NOT EXISTS complaints (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            discord_id INTEGER NOT NULL,
                            message TEXT NOT NULL,
                            category TEXT NOT NULL,
                            complaint TEXT,  -- Content of the message
                            FOREIGN KEY (discord_id) REFERENCES users(discord_id)
                        )
                    """)
                ]

                total_tables = len(tables)

                for i, (table_name, create_sql) in enumerate(tables):
                    await cursor.execute(create_sql)
                    created_tables.append(f"{i + 1}/{total_tables} - 🧑‍💻 {table_name.capitalize()}")

                    progress = ((i + 1) / total_tables) * 100
                    self.conn_database_logger.debug("Creating tables: {:.2f}% completed".format(progress))

                self.conn_database_logger.debug(f"Tables created successfully: {', '.join(created_tables)}")
                self.conn_database_logger.debug(f"🎉 Database created successfully at: {self.db}")

        except aiosqlite.Error as e:
            await self.crash_report_handler.save_error(e)
            self.conn_database_logger.error("🚨 Error while creating database", exc_info=e)

    @asynccontextmanager
    async def get_db_connection(self):
        try:
            await self.create_connection()
            try:
                yield self.connection
            finally:
                await self.close_connection()
        except aiosqlite.Error as e:
            await self.crash_report_handler.save_error(e)
            self.conn_database_logger.error(f"🚨 Error while getting database connection {e}")

    async def create_connection(self) -> None:
        try:
            if self.connection is None:
                self.connection = await aiosqlite.connect(self.db)
                self.conn_database_logger.debug(f"🔌 Connected to database {self.db}")
            else:
                self.conn_database_logger.debug(f"⚡ Connection already exists at: {self.db}")
        except aiosqlite.Error as e:
            await self.crash_report_handler.save_error(e)
            self.conn_database_logger.error("🚨 Error while connecting to database", exc_info=e)

    async def close_connection(self) -> None:
        try:
            if self.connection:
                await self.connection.close()
                self.conn_database_logger.debug(f"🔒 Closed connection to database: {self.db}")
                self.connection = None
            else:
                self.conn_database_logger.debug(f"❌ No connection to close: {self.db}")
        except aiosqlite.Error as e:
            await self.crash_report_handler.save_error(e)
            self.conn_database_logger.error("🚨 Error closing connection", exc_info=e)

    async def schedule_backup(self):
        while True:
            now = datetime.now()
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
            self.conn_database_logger.debug(f"⏳ Waiting for the next database backup in: {time_until_backup}.")

            # Warte bis Mitternacht
            await asyncio.sleep(seconds_until_midnight)

            # Führe das Datenbank-Backup durch
            await self.backup_database()

    async def backup_database(self) -> None:
        """Creates a backup of the current database."""
        try:
            backup_path = f"{self.config.DATABASE_BACKUP_PATH}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)  # Create backup directory if it doesn't exist
            async with aiosqlite.connect(self.db) as source_conn:
                async with aiosqlite.connect(backup_path) as backup_conn:
                    await source_conn.backup(backup_conn)
            self.conn_database_logger.debug(f"💾 Database backed up successfully to {backup_path}")
        except Exception as e:
            await self.crash_report_handler.save_error(e)
            self.conn_database_logger.error("🚨 Error during database backup", exc_info=e)

class AuraCityDatabase(AuraCityDatabaseConnectionHandler):
    def __init__(self) -> None:
        super().__init__()
        self.logger = AuraCityLogger("AuraCityDatabase").get_logger()

    async def add_user(self, discord_id: int, discriminator: str) -> None:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        INSERT INTO users (discord_id, discriminator)
                        VALUES (?, ?)
                        """,
                        (discord_id, discriminator)
                    )
                    await conn.commit()
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error adding user to database", exc_info=e)

    async def get_user_dict(self, discord_id: int) -> Optional[dict]:
        async with (self.get_db_connection() as conn):
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        SELECT * FROM users
                        WHERE discord_id = ?
                        """,
                        (discord_id,)
                    )
                    row = await cursor.fetchone()
                    if row:
                        return {
                            "discord_id": row[1],
                            "username": row[2],
                            "discriminator": row[3]
                        }
                    else:
                        self.logger.debug(f"🔍 User with discord_id {discord_id} not found")
                        return None
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error getting user from database", exc_info=e)
                    return None

    async def get_user(self, discord_id: int) -> Any | None:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        SELECT discord_id FROM users
                        WHERE discord_id = ?
                        """,
                        (discord_id,)
                    )
                    row = await cursor.fetchone()
                    if row:
                        return row[0]
                    else:
                        self.logger.debug(f"🔍 User with discord_id {discord_id} not found")
                        return None
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error getting user from database", exc_info=e)
                    return None


    async def delete_user(self, discord_id: int) -> None:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        DELETE FROM users
                        WHERE discord_id = ?
                        """,
                        (discord_id,)
                    )
                    await conn.commit()
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error deleting user from database", exc_info=e)

    async def add_ban(self, discord_id: int, reason: str) -> None:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        INSERT INTO bans (discord_id, reason)
                        VALUES (?, ?)
                        """,
                        (discord_id, reason)
                    )
                    await conn.commit()
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error adding ban to database", exc_info=e)

    async def get_ban(self, discord_id: int) -> Optional[dict]:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        SELECT * FROM bans
                        WHERE discord_id = ?
                        """,
                        (discord_id,)
                    )
                    row = await cursor.fetchone()
                    if row:
                        return {
                            "discord_id": row[1],
                            "reason": row[2]
                        }
                    else:
                        self.logger.debug(f"🔍 Ban with discord_id {discord_id} not found")
                        return None
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error getting ban from database", exc_info=e)
                    return None

    async def delete_ban(self, discord_id: int) -> None:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        DELETE FROM bans
                        WHERE discord_id = ?
                        """,
                        (discord_id,)
                    )
                    await conn.commit()
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error deleting ban from database", exc_info=e)

    async def add_blacklist(self, discord_id: int, reason: str) -> None:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        INSERT INTO blacklist (discord_id, reason)
                        VALUES (?, ?)
                        """,
                        (discord_id, reason)
                    )
                    await conn.commit()
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error adding blacklist to database", exc_info=e)

    async def get_blacklist(self, discord_id: int) -> Optional[dict]:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        SELECT * FROM blacklist
                        WHERE discord_id = ?
                        """,
                        (discord_id,)
                    )
                    row = await cursor.fetchone()
                    if row:
                        return {
                            "discord_id": row[1],
                            "reason": row[2]
                        }
                    else:
                        self.logger.debug(f"🔍 Blacklist with discord_id {discord_id} not found")
                        return None
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error getting blacklist from database", exc_info=e)
                    return None

    async def delete_blacklist(self, discord_id: int) -> None:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        DELETE FROM blacklist
                        WHERE discord_id = ?
                        """,
                        (discord_id,)
                    )
                    await conn.commit()
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error deleting blacklist from database", exc_info=e)

    async def add_deregistration(self, discord_id: int, time_stamp: str, deregistration_count: int, reason: str, message: str) -> None:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        INSERT INTO deregistrations (discord_id, time_stamp, deregistration_count, reason, message)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (discord_id, time_stamp, deregistration_count, reason, message)
                    )
                    await conn.commit()
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error adding deregistration to database", exc_info=e)

    async def get_deregistration(self, discord_id: int) -> Optional[dict]:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        SELECT * FROM deregistrations
                        WHERE discord_id = ?
                        """,
                        (discord_id,)
                    )
                    row = await cursor.fetchone()
                    if row:
                        return {
                            "discord_id": row[1],
                            "time_stamp": row[2],
                            "deregistration_count": row[3],
                            "reason": row[4],
                            "message": row[5]
                        }
                    else:
                        self.logger.debug(f"🔍 Deregistration with discord_id {discord_id} not found")
                        return None
                except aiosqlite.Error as e:
                    self.logger.error("🚨 Error getting deregistration from database", exc_info=e)
                    return None

    async def delete_deregistration(self, discord_id: int) -> None:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        DELETE FROM deregistrations
                        WHERE discord_id = ?
                        """,
                        (discord_id,)
                    )
                    await conn.commit()
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error deleting deregistration from database", exc_info=e)


    async def add_complaint(self, discord_id: int, message: str, category: str, complaint: str) -> None:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        INSERT INTO complaints (discord_id, message, category, complaint)
                        VALUES (?, ?, ?, ?)
                        """,
                        (discord_id, message, category, complaint)
                    )
                    await conn.commit()
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error adding complaint to database", exc_info=e)

    async def get_complaint(self, discord_id: int) -> Optional[dict]:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        SELECT * FROM complaints
                        WHERE discord_id = ?
                        """,
                        (discord_id,)
                    )
                    row = await cursor.fetchone()
                    if row:
                        return {
                            "discord_id": row[1],
                            "message": row[2],
                            "category": row[3],
                            "complaint": row[4]
                        }
                    else:
                        self.logger.debug(f"🔍 Complaint with discord_id {discord_id} not found")
                        return None
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error getting complaint from database", exc_info=e)
                    return None

    async def delete_complaint(self, discord_id: int) -> None:
        async with self.get_db_connection() as conn:
            async with conn.cursor() as cursor:
                try:
                    await cursor.execute(
                        """
                        DELETE FROM complaints
                        WHERE discord_id = ?
                        """,
                        (discord_id,)
                    )
                    await conn.commit()
                except aiosqlite.Error as e:
                    await self.crash_report_handler.save_error(e)
                    self.logger.error("🚨 Error deleting complaint from database", exc_info=e)
