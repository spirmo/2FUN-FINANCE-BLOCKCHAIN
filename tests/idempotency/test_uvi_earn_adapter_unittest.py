import sqlite3
import tempfile
import unittest
from pathlib import Path

from financial_core.contracts.uvi import UVIValueRequest
from financial_core.integrations.uvi_earn_adapter import UVIEarnAdapter
from platform_core.universal_value.ledger.value_ledger import ValueLedger


class TestUVIEarnAdapterIdempotency(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "uvi_test.db"

        with sqlite3.connect(self.db_path) as connection:
            connection.execute("""
                CREATE TABLE uvi_ledger_entries (
                    transaction_id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    amount TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    transaction_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata_json TEXT NOT NULL
                )
            """)

        self.ledger = ValueLedger(db_path=self.db_path)
        self.adapter = UVIEarnAdapter(self.ledger)

    def tearDown(self):
        self.temp_dir.cleanup()

    def request(self, amount="10", user_id="USER-1", unit="Drika"):
        return UVIValueRequest(
            operation_id="EARN-100",
            user_id=user_id,
            amount=amount,
            unit=unit,
            metadata={},
        )

    def test_replay_returns_original_transaction_without_new_entry(self):
        first = self.adapter.process(self.request())
        second = self.adapter.process(self.request())

        self.assertTrue(first.recorded)
        self.assertTrue(second.recorded)
        self.assertEqual(
            first.metadata["transaction_id"],
            second.metadata["transaction_id"],
        )
        self.assertFalse(first.metadata["idempotent_replay"])
        self.assertTrue(second.metadata["idempotent_replay"])
        self.assertEqual(len(self.ledger.all_entries()), 1)

    def test_replay_accepts_legacy_xp_alias_for_point(self):
        first = self.adapter.process(self.request(unit="XP"))
        second = self.adapter.process(self.request(unit="POINT"))

        self.assertEqual(
            first.metadata["transaction_id"],
            second.metadata["transaction_id"],
        )
        self.assertEqual(len(self.ledger.all_entries()), 1)

    def test_reused_operation_id_with_different_amount_is_rejected(self):
        self.adapter.process(self.request(amount="10"))

        with self.assertRaises(ValueError):
            self.adapter.process(self.request(amount="11"))

        self.assertEqual(len(self.ledger.all_entries()), 1)

    def test_reused_operation_id_with_different_user_is_rejected(self):
        self.adapter.process(self.request(user_id="USER-1"))

        with self.assertRaises(ValueError):
            self.adapter.process(self.request(user_id="USER-2"))

        self.assertEqual(len(self.ledger.all_entries()), 1)


if __name__ == "__main__":
    unittest.main()
