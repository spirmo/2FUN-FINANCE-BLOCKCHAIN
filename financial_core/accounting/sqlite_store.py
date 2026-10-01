"""SQLite-backed accounting entry store."""

import sqlite3
from pathlib import Path

from financial_core.contracts.accounting import AccountingEntry


class SQLiteAccountingEntryStore:
    """
    Persistent storage for accounting entries.

    This store owns accounting records only.
    It does not own balances, UVI state, or blockchain state.
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
                CREATE TABLE IF NOT EXISTS accounting_entries (
                    entry_id TEXT PRIMARY KEY,
                    operation_id TEXT NOT NULL,
                    account_id TEXT NOT NULL,
                    entry_type TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    unit TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    description TEXT,
                    metadata_json TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def get(self, entry_id: str) -> AccountingEntry | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT
                    entry_id,
                    operation_id,
                    account_id,
                    entry_type,
                    amount,
                    unit,
                    direction,
                    description,
                    metadata_json
                FROM accounting_entries
                WHERE entry_id = ?
                """,
                (entry_id,),
            ).fetchone()

        if row is None:
            return None

        import json

        return AccountingEntry(
            entry_id=row[0],
            operation_id=row[1],
            account_id=row[2],
            entry_type=row[3],
            amount=row[4],
            unit=row[5],
            direction=row[6],
            description=row[7],
            metadata=json.loads(row[8]),
        )

    def save(self, entry: AccountingEntry) -> None:
        import json

        with self._connect() as connection:
            connection.execute(
                """
                INSERT OR IGNORE INTO accounting_entries (
                    entry_id,
                    operation_id,
                    account_id,
                    entry_type,
                    amount,
                    unit,
                    direction,
                    description,
                    metadata_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.entry_id,
                    entry.operation_id,
                    entry.account_id,
                    entry.entry_type,
                    entry.amount,
                    entry.unit,
                    entry.direction,
                    entry.description,
                    json.dumps(
                        dict(entry.metadata),
                        sort_keys=True,
                    ),
                ),
            )
            connection.commit()
