"""SQLite persistence for controller registry records."""

import os
import sqlite3
from pathlib import Path
from threading import RLock


def get_database_path() -> Path:
    """Resolve the controller database path from configuration."""
    configured = os.environ.get("DABALLS_DATABASE_PATH")
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".daballs" / "controller.sqlite3"


class SQLiteStateStore:
    """Store serialized Pydantic registry records in SQLite."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path).expanduser()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        with self._connect() as connection:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS jobs (
                    record_id TEXT PRIMARY KEY,
                    record_json TEXT NOT NULL
                )"""
            )
            connection.execute(
                """CREATE TABLE IF NOT EXISTS workers (
                    record_id TEXT PRIMARY KEY,
                    record_json TEXT NOT NULL
                )"""
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    def load_records(self, table: str) -> list[str]:
        self._validate_table(table)
        with self._lock, self._connect() as connection:
            rows = connection.execute(
                f"SELECT record_json FROM {table} ORDER BY rowid"
            ).fetchall()
        return [row[0] for row in rows]

    def save_record(self, table: str, record_id: str, record_json: str) -> None:
        self._validate_table(table)
        with self._lock, self._connect() as connection:
            connection.execute(
                f"""INSERT INTO {table} (record_id, record_json)
                    VALUES (?, ?)
                    ON CONFLICT(record_id) DO UPDATE
                    SET record_json = excluded.record_json""",
                (record_id, record_json),
            )

    def delete_record(self, table: str, record_id: str) -> None:
        """Delete one persisted registry record."""
        self._validate_table(table)
        with self._lock, self._connect() as connection:
            connection.execute(
                f"DELETE FROM {table} WHERE record_id = ?",
                (record_id,),
            )

    def clear_records(self, table: str) -> None:
        self._validate_table(table)
        with self._lock, self._connect() as connection:
            connection.execute(f"DELETE FROM {table}")

    @staticmethod
    def _validate_table(table: str) -> None:
        if table not in {"jobs", "workers"}:
            raise ValueError("Unsupported persistence table")
