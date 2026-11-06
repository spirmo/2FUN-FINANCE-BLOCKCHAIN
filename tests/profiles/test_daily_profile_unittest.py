"""Tests for persistent daily reward profiles."""

import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from financial_core.profiles.daily_profile import DailyProfileStore


class DailyProfileStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "profile.sqlite3"
        self.store = DailyProfileStore(self.db_path)
        self.day = date(2026, 10, 16)

    def tearDown(self):
        self.temp_dir.cleanup()

    def record(self, operation_id, base, value, day=None):
        return self.store.record_activity(
            operation_id=operation_id,
            user_id="user-1",
            activity_date=day or self.day,
            base_points=Decimal(base),
            value_points=Decimal(value),
            reference_price=Decimal("0.01"),
            current_price=Decimal("0.02"),
            reward_unit="POINT",
            uvi_transaction_id=f"uvi-{operation_id}",
        )

    def test_daily_totals_and_lifetime_base_are_separate(self):
        self.record("op-1", "100", "50")
        self.record("op-2", "200", "100")
        self.record("op-3", "30", "15", date(2026, 10, 17))

        summary = self.store.daily_summary("user-1", self.day)

        self.assertEqual(summary["activity_count"], 2)
        self.assertEqual(Decimal(summary["daily_base_points"]), Decimal("300"))
        self.assertEqual(Decimal(summary["daily_value_points"]), Decimal("150"))
        self.assertEqual(
            Decimal(self.store.lifetime_base_points("user-1")),
            Decimal("330"),
        )

    def test_identical_replay_does_not_double_count(self):
        self.assertTrue(self.record("op-1", "100", "50"))
        self.assertFalse(self.record("op-1", "100", "50"))

        summary = self.store.daily_summary("user-1", self.day)
        self.assertEqual(summary["activity_count"], 1)
        self.assertEqual(Decimal(summary["daily_base_points"]), Decimal("100"))

    def test_reusing_operation_id_with_different_data_is_rejected(self):
        self.record("op-1", "100", "50")

        with self.assertRaises(ValueError):
            self.record("op-1", "101", "50")

    def test_prices_must_be_positive(self):
        with self.assertRaises(ValueError):
            self.store.record_activity(
                operation_id="op-bad",
                user_id="user-1",
                activity_date=self.day,
                base_points="10",
                value_points="5",
                reference_price="0",
                current_price="0.02",
                reward_unit="POINT",
                uvi_transaction_id="uvi-op-bad",
            )

    def test_profile_survives_store_recreation(self):
        self.record("op-1", "100", "50")
        reopened = DailyProfileStore(self.db_path)

        self.assertEqual(
            Decimal(reopened.lifetime_base_points("user-1")),
            Decimal("100"),
        )


if __name__ == "__main__":
    unittest.main()
