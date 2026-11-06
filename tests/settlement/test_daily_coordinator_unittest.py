import sqlite3
import tempfile
import unittest
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path

from financial_core.settlement.daily_coordinator import (
    DailySettlementCoordinator,
    SelectionWindowClosed,
    SettlementAlreadyFinalized,
)

UTC = timezone.utc
DAY = date(2026, 10, 17)


class DailySettlementCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = str(Path(self.temp.name) / "settlement.db")
        self._create_schema()
        self.coordinator = DailySettlementCoordinator(self._connect)

    def tearDown(self):
        self.temp.cleanup()

    def _connect(self):
        return sqlite3.connect(self.db, isolation_level=None, timeout=30)

    def _create_schema(self):
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE daily_settlement_choices (
                    user_id TEXT NOT NULL,
                    operational_date TEXT NOT NULL,
                    destination TEXT NOT NULL CHECK (
                        destination IN ('Drika', 'SHIR', 'ΣSHIR', '2FUNC', 'Drik')
                    ),
                    selected_at_utc TEXT NOT NULL,
                    PRIMARY KEY (user_id, operational_date)
                );

                CREATE TABLE daily_settlement_intents (
                    settlement_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    operational_date TEXT NOT NULL,
                    destination TEXT NOT NULL CHECK (
                        destination IN ('Drika', 'SHIR', 'ΣSHIR', '2FUNC', 'Drik')
                    ),
                    status TEXT NOT NULL,
                    trigger_reason TEXT NOT NULL,
                    operation_id TEXT NOT NULL UNIQUE,
                    created_at_utc TEXT NOT NULL,
                    finalized_at_utc TEXT,
                    source_amount TEXT,
                    source_unit TEXT,
                    destination_amount TEXT,
                    reference_price TEXT,
                    current_price TEXT,
                    uvi_transaction_id TEXT,
                    metadata_json TEXT NOT NULL DEFAULT '{}',
                    UNIQUE (user_id, operational_date)
                );
            """)

    def test_selection_window_boundaries(self):
        result = self.coordinator.select_destination(
            user_id="user-1",
            destination="SHIR",
            now=datetime(2026, 10, 17, 22, 30, tzinfo=UTC),
        )
        self.assertEqual(result["destination"], "SHIR")

        with self.assertRaises(SelectionWindowClosed):
            self.coordinator.select_destination(
                user_id="user-2",
                destination="2FUNC",
                now=datetime(2026, 10, 17, 23, 30, tzinfo=UTC),
            )

    def test_drik_is_selectable(self):
        result = self.coordinator.select_destination(
            user_id="user-1",
            destination="Drik",
            now=datetime(2026, 10, 17, 22, 45, tzinfo=UTC),
        )
        self.assertEqual(result["destination"], "Drik")

    def test_choice_survives_restart(self):
        self.coordinator.select_destination(
            user_id="user-1",
            destination="2FUNC",
            now=datetime(2026, 10, 17, 22, 45, tzinfo=UTC),
        )
        restarted = DailySettlementCoordinator(self._connect)
        choice = restarted.get_choice(
            user_id="user-1",
            operational_date=DAY,
        )
        self.assertEqual(choice["destination"], "2FUNC")

    def test_default_drika_and_duplicate_intent(self):
        first = self.coordinator.create_settlement_intent(
            user_id="user-1",
            operational_date=DAY,
            now=datetime(2026, 10, 18, 0, 0, tzinfo=UTC),
        )
        second = self.coordinator.create_settlement_intent(
            user_id="user-1",
            operational_date=DAY,
            now=datetime(2026, 10, 18, 0, 1, tzinfo=UTC),
        )
        self.assertEqual(first["destination"], "Drika")
        self.assertEqual(first["settlement_id"], second["settlement_id"])
        self.assertEqual(first["operation_id"], second["operation_id"])
        self.assertEqual(first["metadata"], second["metadata"])

    def test_completion_is_idempotent_and_rejects_other_transaction(self):
        now = datetime(2026, 10, 18, 0, 0, tzinfo=UTC)
        self.coordinator.create_settlement_intent(
            user_id="user-1",
            operational_date=DAY,
            now=now,
        )
        args = {
            "user_id": "user-1",
            "operational_date": DAY,
            "source_amount": Decimal("10.25"),
            "source_unit": "POINT",
            "destination_amount": Decimal("2.5"),
            "uvi_transaction_id": "uvi-tx-1",
            "now": now,
        }
        first = self.coordinator.mark_transfer_completed(**args)
        second = self.coordinator.mark_transfer_completed(**args)
        self.assertEqual(first["status"], "COMPLETED")
        self.assertEqual(first["uvi_transaction_id"], second["uvi_transaction_id"])

        args["uvi_transaction_id"] = "uvi-tx-2"
        with self.assertRaises(SettlementAlreadyFinalized):
            self.coordinator.mark_transfer_completed(**args)


    def test_same_transaction_with_conflicting_completion_details_is_rejected(self):
        now = datetime(2026, 10, 18, 0, 0, tzinfo=UTC)
        self.coordinator.create_settlement_intent(
            user_id="user-1",
            operational_date=DAY,
            now=now,
        )
        args = {
            "user_id": "user-1",
            "operational_date": DAY,
            "source_amount": Decimal("10.25"),
            "source_unit": "POINT",
            "destination_amount": Decimal("2.5"),
            "reference_price": Decimal("1.2"),
            "current_price": Decimal("1.1"),
            "uvi_transaction_id": "uvi-tx-1",
            "now": now,
        }
        self.coordinator.mark_transfer_completed(**args)

        conflicting_fields = (
            ("source_amount", Decimal("11.25")),
            ("source_unit", "Drika"),
            ("destination_amount", Decimal("3.5")),
            ("reference_price", Decimal("1.3")),
            ("current_price", Decimal("1.4")),
        )
        for field, conflicting_value in conflicting_fields:
            changed_args = dict(args)
            changed_args[field] = conflicting_value
            with self.subTest(field=field):
                with self.assertRaises(SettlementAlreadyFinalized):
                    self.coordinator.mark_transfer_completed(**changed_args)


if __name__ == "__main__":
    unittest.main()
