"""SQLite-backed persistent integrity record store."""

import sqlite3
from pathlib import Path

from financial_core.contracts.integrity_store import IntegrityRecord


class SQLiteIntegrityRecordStore:
    """
    Durable storage for integrity records.

    This store owns integrity records only.
    It does not own financial balances or blockchain state.
    """

    def __init__(self, database_path: str | Path):
        self._database_path = str(database_path)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self._database_path)

    def _initialize(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS integrity_records (
                    operation_id TEXT PRIMARY KEY,
                    operation_type TEXT NOT NULL,
                    integrity_version TEXT NOT NULL,
                    algorithm TEXT NOT NULL,
                    hash_value TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    source TEXT NOT NULL,
                    actor TEXT,
                    origin TEXT,
                    target TEXT
                )
                """
            )
            connection.commit()

    def get(self, operation_id: str) -> IntegrityRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    operation_id,
                    operation_type,
                    integrity_version,
                    algorithm,
                    hash_value,
                    previous_hash,
                    source,
                    actor,
                    origin,
                    target
                FROM integrity_records
                WHERE operation_id = ?
                """,
                (operation_id,),
            ).fetchone()

        if row is None:
            return None

        return IntegrityRecord(
            operation_id=row[0],
            operation_type=row[1],
            integrity_version=row[2],
            algorithm=row[3],
            hash_value=row[4],
            previous_hash=row[5],
            source=row[6],
            actor=row[7],
            origin=row[8],
            target=row[9],
        )

    def save(self, record: IntegrityRecord) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO integrity_records (
                    operation_id,
                    operation_type,
                    integrity_version,
                    algorithm,
                    hash_value,
                    previous_hash,
                    source,
                    actor,
                    origin,
                    target
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.operation_id,
                    record.operation_type,
                    record.integrity_version,
                    record.algorithm,
                    record.hash_value,
                    record.previous_hash,
                    record.source,
                    record.actor,
                    record.origin,
                    record.target,
                ),
            )
            connection.commit()
