"""SQLite-backed persistent idempotency store."""

import json
import sqlite3
from pathlib import Path

from financial_core.contracts.transfer_execution import (
    TransferExecutionResult,
)


class SQLiteIdempotencyStore:
    """
    Durable idempotency store.

    This store owns only idempotency records.
    It is not a financial ledger and does not own balances.
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
                CREATE TABLE IF NOT EXISTS idempotency_results (
                    operation_id TEXT PRIMARY KEY,
                    result_json TEXT NOT NULL
                )
                """
            )
            connection.commit()

    def get(
        self,
        operation_id: str,
    ) -> TransferExecutionResult | None:
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

        return TransferExecutionResult(
            operation_id=data["operation_id"],
            transfer_id=data["transfer_id"],
            source_account_id=data["source_account_id"],
            destination_account_id=data["destination_account_id"],
            amount=data["amount"],
            unit=data["unit"],
            status=data["status"],
            source_uvi_transaction_id=data.get(
                "source_uvi_transaction_id"
            ),
            destination_uvi_transaction_id=data.get(
                "destination_uvi_transaction_id"
            ),
            financial_transaction_hash=data.get(
                "financial_transaction_hash"
            ),
            metadata=data.get("metadata"),
        )

    def save(
        self,
        operation_id: str,
        result: TransferExecutionResult,
    ) -> None:
        data = {
            "operation_id": result.operation_id,
            "transfer_id": result.transfer_id,
            "source_account_id": result.source_account_id,
            "destination_account_id": result.destination_account_id,
            "amount": result.amount,
            "unit": result.unit,
            "status": result.status,
            "source_uvi_transaction_id":
                result.source_uvi_transaction_id,
            "destination_uvi_transaction_id":
                result.destination_uvi_transaction_id,
            "financial_transaction_hash":
                result.financial_transaction_hash,
            "metadata": dict(result.metadata or {}),
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
                    json.dumps(
                        data,
                        sort_keys=True,
                    ),
                ),
            )
            connection.commit()
