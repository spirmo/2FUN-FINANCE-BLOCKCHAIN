"""Integration tests for RewardExecutor with the real OS UVI ledger."""

import sqlite3
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

from financial_core.contracts.reward_execution import RewardExecutionRequest
from financial_core.idempotency.generic_sqlite_store import (
    GenericSQLiteIdempotencyStore,
)
from financial_core.integrations.uvi_earn_adapter import UVIEarnAdapter
from financial_core.profiles.daily_profile import DailyProfileStore
from financial_core.rewards.executor import RewardExecutor
from financial_core.valuation.twofunc_base_price_provider import TwofuncBasePriceProvider
from platform_core.universal_value.ledger.value_ledger import ValueLedger


class FakeIntegrityProvider:
    """Keep this test focused on Reward-to-UVI integration."""

    def generate(self, request):
        return SimpleNamespace(
            hash_value=f"test-integrity-{request.operation_id}"
        )


class RewardRealUVIIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        self.uvi_db = root / "uvi.sqlite3"
        with sqlite3.connect(self.uvi_db) as connection:
            connection.execute(
                """
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
                """
            )

        self.ledger = ValueLedger(db_path=self.uvi_db)
        self.uvi_adapter = UVIEarnAdapter(self.ledger)

        self.profile = DailyProfileStore(root / "profile.sqlite3")
        self.idempotency = GenericSQLiteIdempotencyStore(
            root / "idempotency.sqlite3"
        )

        self.executor = RewardExecutor(
            valuation_provider=TwofuncBasePriceProvider(),
            uvi_adapter=self.uvi_adapter,
            idempotency_store=self.idempotency,
            integrity_provider=FakeIntegrityProvider(),
            profile_store=self.profile,
            activity_date_provider=lambda: date(2026, 10, 16),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_request(self):
        return RewardExecutionRequest(
            operation_id="reward-uvi-001",
            user_id="user-uvi-001",
            base_reward=Decimal("100"),
            reference_price=Decimal("0"),
            current_price=Decimal("0"),
            reward_unit="POINT",
            valuation_asset="2FUNC",
            quote_asset="USD",
            metadata={"integration_test": True},
        )

    def test_reward_records_once_in_real_uvi_and_replays_idempotently(self):
        request = self.make_request()

        first = self.executor.execute(request)

        self.assertEqual(first.status, "RECORDED")
        self.assertFalse(hasattr(first, "reference_price"))
        self.assertFalse(hasattr(first, "current_price"))
        self.assertEqual(first.metadata, {"integrity_verified": False})
        self.assertFalse(first.idempotent)
        self.assertEqual(first.adjusted_reward, Decimal("100"))

        entries = self.ledger.all_entries()
        self.assertEqual(len(entries), 1)

        entry = entries[0]
        self.assertEqual(entry.event_id, request.operation_id)
        self.assertEqual(entry.user_id, request.user_id)
        self.assertEqual(Decimal(str(entry.amount)), Decimal("100"))
        self.assertEqual(entry.transaction_type, "EARN")
        self.assertEqual(entry.transaction_id, first.uvi_transaction_id)

        entry_metadata = dict(entry.metadata or {})
        self.assertEqual(
            entry_metadata.get("financial_core_operation_id"),
            request.operation_id,
        )

        summary = self.profile.daily_summary(
            request.user_id,
            date(2026, 10, 16),
        )
        self.assertEqual(summary["activity_count"], 1)
        self.assertEqual(
            Decimal(summary["daily_base_points"]),
            Decimal("100"),
        )
        self.assertEqual(
            Decimal(summary["daily_value_points"]),
            Decimal("100"),
        )

        second = self.executor.execute(request)

        self.assertTrue(second.idempotent)
        self.assertFalse(hasattr(second, "reference_price"))
        self.assertFalse(hasattr(second, "current_price"))
        self.assertEqual(second.metadata, {"integrity_verified": False})
        self.assertEqual(
            second.uvi_transaction_id,
            first.uvi_transaction_id,
        )
        self.assertEqual(len(self.ledger.all_entries()), 1)

        replay_summary = self.profile.daily_summary(
            request.user_id,
            date(2026, 10, 16),
        )
        self.assertEqual(replay_summary["activity_count"], 1)
        self.assertEqual(
            Decimal(self.profile.lifetime_base_points(request.user_id)),
            Decimal("100"),
        )


if __name__ == "__main__":
    unittest.main()
