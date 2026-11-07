import json
import sqlite3
import tempfile
import unittest
from contextlib import closing

from datetime import datetime, timezone
from pathlib import Path

from platform_core.universal_value.ledger.value_ledger import ValueLedger
from financial_core.settlement.daily_service import DailySettlementService


class CountingLedger:
    def __init__(self, ledger):
        self.ledger = ledger
        self.calls = 0

    def user_entries(self, user_id, connection=None):
        self.calls += 1
        return self.ledger.user_entries(
            user_id, connection=connection
        )


class DailySettlementServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = str(Path(self.temp_dir.name) / "test.db")

        self.now = datetime(
            2026, 11, 7, 12, 0, tzinfo=timezone.utc
        )
        self.day = "2026-11-06"
        self.user_id = "user-1"

        self._create_schema()

        self.ledger = ValueLedger(db_path=self.db_path)
        self.service = DailySettlementService(
            self._connect, self.ledger
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _connect(self):
        return sqlite3.connect(self.db_path, timeout=30)

    def _create_schema(self):
        with closing(sqlite3.connect(self.db_path)) as connection, connection:
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

                CREATE TABLE daily_settlement_choices (
                    user_id TEXT NOT NULL,
                    operational_date TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    selected_at_utc TEXT NOT NULL,
                    PRIMARY KEY (user_id, operational_date)
                );

                CREATE TABLE daily_settlement_intents (
                    settlement_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    operational_date TEXT NOT NULL,
                    destination TEXT NOT NULL,
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

                CREATE TABLE daily_point_remainders (
                    user_id TEXT NOT NULL,
                    operational_date TEXT NOT NULL,
                    remainder_points TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL,
                    PRIMARY KEY (user_id, operational_date),
                    CHECK (
                        CAST(remainder_points AS NUMERIC) >= 0
                        AND CAST(remainder_points AS NUMERIC) < 4
                    )
                );

                CREATE TABLE daily_point_settlements (
                    user_id TEXT NOT NULL,
                    operational_date TEXT NOT NULL,
                    daily_points TEXT NOT NULL,
                    carry_in_points TEXT NOT NULL,
                    drika_amount TEXT NOT NULL,
                    remainder_points TEXT NOT NULL,
                    created_at_utc TEXT NOT NULL,
                    PRIMARY KEY (user_id, operational_date),
                    CHECK (CAST(daily_points AS NUMERIC) >= 0),
                    CHECK (
                        CAST(carry_in_points AS NUMERIC) >= 0
                        AND CAST(carry_in_points AS NUMERIC) < 4
                    ),
                    CHECK (CAST(drika_amount AS NUMERIC) >= 0),
                    CHECK (
                        CAST(remainder_points AS NUMERIC) >= 0
                        AND CAST(remainder_points AS NUMERIC) < 4
                    )
                );
            """)

    def _insert_entry(
        self, transaction_id, amount, timestamp,
        *, currency="POINT", transaction_type="EARN",
        metadata=None, user_id=None,
    ):
        metadata = metadata or {
            "value_flow": "POINT_TO_2FUNC",
            "activity_validated": True,
            "fraud_invalidated": False,
        }

        with closing(sqlite3.connect(self.db_path)) as connection, connection:
            connection.execute("""
                INSERT INTO uvi_ledger_entries (
                    transaction_id, event_id, user_id, amount,
                    currency, transaction_type, timestamp,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                transaction_id,
                f"event-{transaction_id}",
                user_id or self.user_id,
                str(amount),
                currency,
                transaction_type,
                timestamp,
                json.dumps(metadata),
            ))

    def _insert_previous_remainder(self, remainder):
        with closing(sqlite3.connect(self.db_path)) as connection, connection:
            connection.execute("""
                INSERT INTO daily_point_remainders (
                    user_id, operational_date,
                    remainder_points, updated_at_utc
                ) VALUES (?, ?, ?, ?)
            """, (
                self.user_id,
                "2026-11-05",
                str(remainder),
                "2026-11-06T00:00:00+00:00",
            ))

    def test_timezone_offsets_and_remainder_are_calculated_correctly(self):
        # UTC: 2026-11-05 22:30 — خارج از روز عملیاتی
        self._insert_entry(
            "before-day", "100", "2026-11-06T00:30:00+02:00"
        )

        # UTC: 2026-11-06 21:30 — داخل روز عملیاتی
        self._insert_entry(
            "inside-day", "5.5", "2026-11-06T23:30:00+02:00"
        )

        # روز بعد از بازه
        self._insert_entry(
            "after-day", "200", "2026-11-07T01:00:00+00:00"
        )

        # فعالیت تأییدنشده نباید محاسبه شود.
        self._insert_entry(
            "unvalidated", "50",
            "2026-11-06T10:00:00+00:00",
            metadata={
                "value_flow": "POINT_TO_2FUNC",
                "activity_validated": False,
            },
        )

        self._insert_previous_remainder("3")

        result = self.service.create_previous_day_intent(
            self.user_id, self.now
        )

        self.assertEqual(result["status"], "created")

        metadata = json.loads(
            result["settlement"]["metadata_json"]
        )

        self.assertEqual(metadata["daily_points"], "5.5")
        self.assertEqual(metadata["carry_in_points"], "3")
        self.assertEqual(metadata["drika_amount"], "2")
        self.assertEqual(metadata["remainder_points"], "0.5")

        with closing(sqlite3.connect(self.db_path)) as connection, connection:
            settlement = connection.execute("""
                SELECT daily_points, carry_in_points,
                       drika_amount, remainder_points
                FROM daily_point_settlements
                WHERE user_id = ? AND operational_date = ?
            """, (self.user_id, self.day)).fetchone()

            remainder = connection.execute("""
                SELECT remainder_points
                FROM daily_point_remainders
                WHERE user_id = ? AND operational_date = ?
            """, (self.user_id, self.day)).fetchone()

        self.assertEqual(
            tuple(settlement), ("5.5", "3", "2", "0.5")
        )
        self.assertEqual(remainder[0], "0.5")

    def test_large_point_amounts_preserve_decimal_precision(self):
        self._insert_entry(
            "large-entry",
            "999999999999999999999999999999999999.999999",
            "2026-11-06T12:00:00+00:00",
        )
        self._insert_entry(
            "small-entry",
            "0.000002",
            "2026-11-06T13:00:00+00:00",
        )
        self._insert_previous_remainder("0.000001")

        result = self.service.create_previous_day_intent(
            self.user_id, self.now
        )

        self.assertEqual(result["status"], "created")
        metadata = json.loads(
            result["settlement"]["metadata_json"]
        )

        self.assertEqual(
            metadata["daily_points"],
            "1000000000000000000000000000000000000.000001",
        )
        self.assertEqual(metadata["carry_in_points"], "0.000001")
        self.assertEqual(
            metadata["drika_amount"],
            "250000000000000000000000000000000000",
        )
        self.assertEqual(metadata["remainder_points"], "0.000002")

    def test_repeated_request_does_not_read_ledger_again(self):
        counting_ledger = CountingLedger(self.ledger)
        service = DailySettlementService(
            self._connect, counting_ledger
        )

        first = service.create_previous_day_intent(
            self.user_id, self.now
        )
        second = service.create_previous_day_intent(
            self.user_id, self.now
        )

        self.assertEqual(first["status"], "created")
        self.assertEqual(second["status"], "existing")
        self.assertEqual(
            first["settlement"]["settlement_id"],
            second["settlement"]["settlement_id"],
        )
        self.assertEqual(counting_ledger.calls, 1)

        expected_operation_id = __import__("uuid").uuid5(
            __import__("uuid").NAMESPACE_URL,
            f"2FUN:daily-settlement:{self.user_id}:{self.day}",
        )

        self.assertEqual(
            first["settlement"]["operation_id"],
            str(expected_operation_id),
        )

    def test_intent_failure_rolls_back_remainder_and_settlement(self):
        self._insert_entry(
            "valid-entry", "5",
            "2026-11-06T12:00:00+00:00",
        )

        with closing(sqlite3.connect(self.db_path)) as connection, connection:
            connection.execute("""
                CREATE TRIGGER reject_daily_intent
                BEFORE INSERT ON daily_settlement_intents
                BEGIN
                    SELECT RAISE(ABORT, 'forced test failure');
                END;
            """)

        with self.assertRaises(sqlite3.IntegrityError):
            self.service.create_previous_day_intent(
                self.user_id, self.now
            )

        with closing(sqlite3.connect(self.db_path)) as connection, connection:
            settlement_count = connection.execute("""
                SELECT COUNT(*) FROM daily_point_settlements
                WHERE user_id = ? AND operational_date = ?
            """, (self.user_id, self.day)).fetchone()[0]

            remainder_count = connection.execute("""
                SELECT COUNT(*) FROM daily_point_remainders
                WHERE user_id = ? AND operational_date = ?
            """, (self.user_id, self.day)).fetchone()[0]

            intent_count = connection.execute("""
                SELECT COUNT(*) FROM daily_settlement_intents
                WHERE user_id = ? AND operational_date = ?
            """, (self.user_id, self.day)).fetchone()[0]

        self.assertEqual(settlement_count, 0)
        self.assertEqual(remainder_count, 0)
        self.assertEqual(intent_count, 0)

    def test_invalid_timestamp_fails_closed_and_rolls_back(self):
        self._insert_entry(
            "bad-time", "5", "not-a-valid-timestamp"
        )

        with self.assertRaises(ValueError):
            self.service.create_previous_day_intent(
                self.user_id, self.now
            )

        with closing(sqlite3.connect(self.db_path)) as connection, connection:
            count = connection.execute("""
                SELECT COUNT(*) FROM daily_point_settlements
                WHERE user_id = ? AND operational_date = ?
            """, (self.user_id, self.day)).fetchone()[0]

        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
