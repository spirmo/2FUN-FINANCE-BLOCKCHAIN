"""EX-011 Internal transfer executor tests."""

import sqlite3
import tempfile
import unittest
from pathlib import Path
from decimal import Decimal

from financial_core.internal.contracts import InternalTransferRequest
from financial_core.internal.executor import InternalTransferExecutor
from platform_core.universal_value.ledger.value_ledger import ValueLedger


class TestInternalTransferExecutor(unittest.TestCase):
    def setUp(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._temp_dir.cleanup)
        self._db_path = Path(self._temp_dir.name) / "uvi.sqlite3"

        with sqlite3.connect(self._db_path) as connection:
            connection.executescript("""
                CREATE TABLE uvi_ledger_entries (
                    transaction_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata_json TEXT NOT NULL DEFAULT '{}'
                );
                CREATE TABLE uvi_transfer_operations (
                    operation_id TEXT PRIMARY KEY,
                    source_user_id TEXT NOT NULL,
                    destination_user_id TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    debit_transaction_id TEXT NOT NULL UNIQUE,
                    credit_transaction_id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL
                );
            """)

    def test_internal_transfer_moves_value_between_users(self):
        ledger = ValueLedger(db_path=self._db_path)

        ledger.record(
            transaction_id="INITIAL-INT-001",
            event_id="INITIAL-EVENT-INT-001",
            user_id="USER-001",
            amount=Decimal("100"),
            currency="Drika",
            transaction_type="CREDIT",
            metadata={"source": "E2E_TEST"},
        )

        request = InternalTransferRequest(
            operation_id="INT-001",
            source_user_id="USER-001",
            target_user_id="USER-002",
            amount="40",
            unit="Drika",
            metadata={"test": "EX-011"},
        )

        record = InternalTransferExecutor(ledger).execute(request)

        self.assertEqual(record.operation_id, "INT-001")
        self.assertEqual(record.source_user_id, "USER-001")
        self.assertEqual(record.target_user_id, "USER-002")
        self.assertEqual(record.amount, "40")
        self.assertEqual(record.unit, "Drika")
        self.assertEqual(record.status, "TRANSFERRED")

        self.assertIsNotNone(record.source_transaction_id)
        self.assertIsNotNone(record.target_transaction_id)

        self.assertEqual(
            ledger.balance("USER-001", "Drika"),
            Decimal("60"),
        )
        self.assertEqual(
            ledger.balance("USER-002", "Drika"),
            Decimal("40"),
        )

        entries = ledger.all_entries()
        self.assertEqual(len(entries), 3)

        self.assertEqual(
            entries[1].transaction_type,
            "DEBIT",
        )
        self.assertEqual(
            entries[2].transaction_type,
            "CREDIT",
        )

    def test_insufficient_balance_is_rejected(self):
        ledger = ValueLedger(db_path=self._db_path)

        ledger.record(
            transaction_id="INITIAL-INT-002",
            event_id="INITIAL-EVENT-INT-002",
            user_id="USER-001",
            amount=Decimal("10"),
            currency="Drika",
            transaction_type="CREDIT",
        )

        request = InternalTransferRequest(
            operation_id="INT-002",
            source_user_id="USER-001",
            target_user_id="USER-002",
            amount="20",
            unit="Drika",
        )

        with self.assertRaises(ValueError):
            InternalTransferExecutor(ledger).execute(request)

        self.assertEqual(
            ledger.balance("USER-001", "Drika"),
            Decimal("10"),
        )
        self.assertEqual(
            ledger.balance("USER-002", "Drika"),
            Decimal("0"),
        )


if __name__ == "__main__":
    unittest.main()
