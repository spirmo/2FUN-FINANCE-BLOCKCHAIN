"""Generic SQLite-backed persistent idempotency store."""

import json
import sqlite3
from pathlib import Path

from financial_core.contracts.idempotency import (
    GenericIdempotencyStore,
    IdempotencyRecord,
)


class GenericSQLiteIdempotencyStore(GenericIdempotencyStore):
    """Durable idempotency store for generic financial operations.

    This store owns execution identity only.
    Financial balances remain owned by their existing authority.
    """

    def __init__(self, database_path: str | Path):
        self._database_path = str(database_path)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self._database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS idempotency_results (
                    operation_id TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def get(self, operation_id: str) -> IdempotencyRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT result_json
                FROM idempotency_results
                WHERE operation_id = ?
                """,
                (operation_id,),
            ).fetchone()

        if row is None:
            return None

        data = json.loads(row[0])

        return IdempotencyRecord(
            operation_id=data["operation_id"],
            operation_type=data["operation_type"],
            result=data["result"],
        )

    def save(
        self,
        operation_id: str,
        record: IdempotencyRecord,
    ) -> None:
        data = {
            "operation_id": record.operation_id,
            "operation_type": record.operation_type,
            "result": dict(record.result),
        }

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO idempotency_results (
                    operation_id,
                    result_json
                )
                VALUES (?, ?)
                """,
                (
                    operation_id,
                    json.dumps(data, sort_keys=True, default=str),
                ),
            )
            connection.commit()
