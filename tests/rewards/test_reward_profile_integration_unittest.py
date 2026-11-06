"""Integration tests for RewardExecutor and DailyProfileStore."""

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
from financial_core.profiles.daily_profile import DailyProfileStore
from financial_core.rewards.executor import RewardExecutor


class FakeUVIAdapter:
    def __init__(self):
        self.calls = 0

    def process(self, request):
        self.calls += 1
        return SimpleNamespace(
            status="RECORDED",
            metadata={"transaction_id": f"uvi-tx-{request.operation_id}"},
        )


class FakeIntegrityProvider:
    def generate(self, request):
        return SimpleNamespace(hash_value=f"hash-{request.operation_id}")


class RewardProfileIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        self.profile = DailyProfileStore(root / "profile.sqlite3")
        self.idempotency = GenericSQLiteIdempotencyStore(
            root / "idempotency.sqlite3"
        )
        self.uvi = FakeUVIAdapter()

        self.executor = RewardExecutor(
            valuation_provider=None,
            uvi_adapter=self.uvi,
            idempotency_store=self.idempotency,
            integrity_provider=FakeIntegrityProvider(),
            profile_store=self.profile,
            activity_date_provider=lambda: date(2026, 10, 16),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_request(self):
        return RewardExecutionRequest(
            operation_id="reward-001",
            user_id="user-001",
            base_reward=Decimal("100"),
            reference_price=Decimal("0.01"),
            current_price=Decimal("0.02"),
            reward_unit="POINT",
            valuation_asset="2FUNC",
            quote_asset="STABLECOIN",
            metadata={"test": True},
        )

    def test_reward_is_recorded_in_daily_profile(self):
        result = self.executor.execute(self.make_request())

        self.assertEqual(result.status, "RECORDED")
        self.assertEqual(result.base_reward, Decimal("100"))
        self.assertEqual(result.adjusted_reward, Decimal("50"))

        summary = self.profile.daily_summary(
            "user-001", date(2026, 10, 16)
        )
        self.assertEqual(summary["activity_count"], 1)
        self.assertEqual(
            Decimal(summary["daily_base_points"]), Decimal("100")
        )
        self.assertEqual(
            Decimal(summary["daily_value_points"]), Decimal("50")
        )
        self.assertEqual(
            Decimal(self.profile.lifetime_base_points("user-001")),
            Decimal("100"),
        )

    def test_replaying_reward_does_not_double_count(self):
        first = self.executor.execute(self.make_request())
        second = self.executor.execute(self.make_request())

        self.assertFalse(first.idempotent)
        self.assertTrue(second.idempotent)
        self.assertEqual(self.uvi.calls, 1)

        summary = self.profile.daily_summary(
            "user-001", date(2026, 10, 16)
        )
        self.assertEqual(summary["activity_count"], 1)
        self.assertEqual(
            Decimal(self.profile.lifetime_base_points("user-001")),
            Decimal("100"),
        )


if __name__ == "__main__":
    unittest.main()
