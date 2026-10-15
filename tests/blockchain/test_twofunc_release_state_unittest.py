import tempfile
import unittest
from datetime import date
from pathlib import Path
import sqlite3
from contextlib import closing

from financial_core.blockchain.twofunc_release_schedule import (
    ReleaseStage,
    TwoFuncReleaseSchedule,
)
from financial_core.blockchain.twofunc_release_state import (
    ReleaseStateError,
    TwoFuncReleaseState,
)
from financial_core.blockchain.twofunc_supply import (
    MAX_SUPPLY,
    MAX_SUPPLY_BASE_UNITS,
    BASE_UNITS_PER_2FUNC,
)


def make_schedule():
    start = date(2026, 1, 1)
    stages = []

    for number in range(1, 11):
        month_index = start.year * 12 + start.month - 1
        month_index += (number - 1) * 6
        year, month_zero = divmod(month_index, 12)

        stages.append(
            ReleaseStage(
                number=number,
                start_date=date(year, month_zero + 1, 1),
                amount=MAX_SUPPLY // 10,
            )
        )

    # The complete supply must be allocated exactly.
    stages[-1] = ReleaseStage(
        number=10,
        start_date=stages[-1].start_date,
        amount=MAX_SUPPLY - sum(stage.amount for stage in stages[:-1]),
    )

    return TwoFuncReleaseSchedule(stages)


class TwoFuncReleaseStateTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "release-test.db"

        # Explicit test-only schema setup. Production schema is owned by
        # the 2FUN-OS database migration, not by TwoFuncReleaseState.
        with closing(sqlite3.connect(self.db_path)) as connection, connection:
            connection.execute(
                """
                CREATE TABLE release_stage_state (
                    stage_number INTEGER PRIMARY KEY
                        CHECK (stage_number BETWEEN 1 AND 10),
                    started_on TEXT,
                    issued_amount TEXT NOT NULL DEFAULT '0'
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE release_issuance_records (
                    tx_id TEXT PRIMARY KEY,
                    stage_number INTEGER NOT NULL,
                    amount TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    FOREIGN KEY (stage_number)
                        REFERENCES release_stage_state(stage_number)
                )
                """
            )
            connection.executemany(
                """
                INSERT INTO release_stage_state
                    (stage_number, started_on, issued_amount)
                VALUES (?, NULL, '0')
                """,
                [(number,) for number in range(1, 11)],
            )

        self.state = TwoFuncReleaseState(self.db_path)
        self.schedule = make_schedule()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_initial_state_has_ten_unactivated_stages(self):
        snapshot = self.state.snapshot()

        self.assertEqual(len(snapshot), 10)
        self.assertIsNone(self.state.active_stage_number())
        self.assertTrue(
            all(item["started_on"] is None for item in snapshot.values())
        )
        self.assertEqual(self.state.issuance_total(), 0)

    def test_first_stage_can_only_be_activated_once(self):
        self.state.activate_first_stage(date(2026, 1, 1))

        with self.assertRaises(ReleaseStateError):
            self.state.activate_first_stage(date(2026, 1, 2))

    def test_next_stage_requires_ninety_percent_and_six_months(self):
        self.state.activate_first_stage(date(2026, 1, 1))

        allocation = self.schedule.stage(1).amount
        self.state.record_issuance(
            self.schedule,
            tx_id="tx-90-percent",
            stage_number=1,
            amount=(allocation * 90 // 100) * BASE_UNITS_PER_2FUNC,
            recorded_on=date(2026, 7, 1),
        )

        self.assertIsNone(
            self.state.next_stage_eligible(
                self.schedule, date(2026, 6, 30)
            )
        )

        eligible = self.state.next_stage_eligible(
            self.schedule, date(2026, 7, 1)
        )
        self.assertEqual(eligible, 2)

    def test_cannot_activate_next_stage_before_both_gates_pass(self):
        self.state.activate_first_stage(date(2026, 1, 1))

        with self.assertRaises(ReleaseStateError):
            self.state.activate_next_stage(
                self.schedule, date(2026, 7, 1)
            )

    def test_duplicate_transaction_id_is_rejected(self):
        self.state.activate_first_stage(date(2026, 1, 1))

        kwargs = dict(
            schedule=self.schedule,
            tx_id="duplicate-tx",
            stage_number=1,
            amount=BASE_UNITS_PER_2FUNC,
            recorded_on=date(2026, 1, 2),
        )

        self.state.record_issuance(**kwargs)

        with self.assertRaises(ReleaseStateError):
            self.state.record_issuance(**kwargs)

        self.assertEqual(
            self.state.issuance_total(), BASE_UNITS_PER_2FUNC
        )

    def test_issuance_cannot_exceed_stage_allocation(self):
        self.state.activate_first_stage(date(2026, 1, 1))

        with self.assertRaises(ReleaseStateError):
            self.state.record_issuance(
                self.schedule,
                tx_id="over-allocation",
                stage_number=1,
                amount=(
                    self.schedule.stage(1).amount + 1
                ) * BASE_UNITS_PER_2FUNC,
                recorded_on=date(2026, 1, 2),
            )

        self.assertEqual(self.state.issuance_total(), 0)

    def test_inactive_stage_cannot_record_issuance(self):
        with self.assertRaises(ReleaseStateError):
            self.state.record_issuance(
                self.schedule,
                tx_id="inactive-stage",
                stage_number=2,
                amount=BASE_UNITS_PER_2FUNC,
                recorded_on=date(2026, 7, 1),
            )

    def test_state_persists_after_reopening_database(self):
        self.state.activate_first_stage(date(2026, 1, 1))
        self.state.record_issuance(
            self.schedule,
            tx_id="persistent-tx",
            stage_number=1,
            amount=BASE_UNITS_PER_2FUNC,
            recorded_on=date(2026, 1, 2),
        )

        reopened = TwoFuncReleaseState(self.db_path)

        self.assertEqual(reopened.active_stage_number(), 1)
        self.assertEqual(
            reopened.issuance_total(), BASE_UNITS_PER_2FUNC
        )

    def test_supply_cap_is_measured_in_base_units(self):
        self.assertEqual(
            MAX_SUPPLY_BASE_UNITS,
            MAX_SUPPLY * BASE_UNITS_PER_2FUNC,
        )


if __name__ == "__main__":
    unittest.main()
