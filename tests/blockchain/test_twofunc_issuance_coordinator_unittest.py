"""Tests for the persistent 2FUNC issuance coordinator."""

import sqlite3
import tempfile
import unittest
from contextlib import closing
from datetime import date
from pathlib import Path

from financial_core.interfaces.native_ledger import (
    DuplicateTransaction,
)
from financial_core.blockchain.persistent_native_ledger import (
    SQLiteNativeLedger,
)
from financial_core.twofunc.issuance_coordinator import (
    IssuanceCoordinatorError,
    TwoFuncIssuanceCoordinator,
)
from financial_core.twofunc.release_schedule import (
    ReleaseStage,
    TwoFuncReleaseSchedule,
)
from financial_core.twofunc.release_state import (
    ReleaseStateError,
    TwoFuncReleaseState,
)
from financial_core.twofunc.supply import (
    MAX_SUPPLY,
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

    stages[-1] = ReleaseStage(
        number=10,
        start_date=stages[-1].start_date,
        amount=MAX_SUPPLY - sum(stage.amount for stage in stages[:-1]),
    )
    return TwoFuncReleaseSchedule(stages)


class TwoFuncIssuanceCoordinatorTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)
        self.release_db = root / "release.db"
        self.ledger_db = root / "ledger.db"
        self.schedule = make_schedule()

        with closing(sqlite3.connect(self.release_db)) as connection:
            with connection:
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

        self.state = TwoFuncReleaseState(self.release_db)
        self.state.activate_first_stage(date(2026, 1, 1))
        self.ledger = SQLiteNativeLedger(str(self.ledger_db))
        self.coordinator = TwoFuncIssuanceCoordinator(
            self.ledger,
            self.state,
            self.schedule,
        )
        self.amount = 1000  # Small test amount in native base units.

    def tearDown(self):
        self.ledger.close()
        self.temp_dir.cleanup()

    def test_issue_records_ledger_and_release_state(self):
        result = self.coordinator.issue(
            tx_id="issue-001",
            recipient="account-A",
            stage_number=1,
            amount=self.amount,
            recorded_on=date(2026, 1, 2),
        )

        self.assertEqual(result, self.ledger.issuance_for("issue-001"))
        self.assertEqual(self.ledger.balance_of("account-A"), self.amount)
        self.assertEqual(
            self.state.issuance_record("issue-001")["amount"],
            self.amount,
        )
        self.assertEqual(self.state.issuance_total(), self.amount)

    def test_retry_does_not_issue_twice(self):
        kwargs = dict(
            tx_id="issue-retry",
            recipient="account-A",
            stage_number=1,
            amount=self.amount,
            recorded_on=date(2026, 1, 2),
        )

        first = self.coordinator.issue(**kwargs)
        second = self.coordinator.issue(**kwargs)

        self.assertEqual(first, second)
        self.assertEqual(self.ledger.balance_of("account-A"), self.amount)
        self.assertEqual(self.ledger.issued_supply, self.amount)
        self.assertEqual(self.state.issuance_total(), self.amount)

    def test_retry_recovers_ledger_commit_without_release_record(self):
        self.ledger.issue_to(
            "issue-interrupted",
            "account-A",
            self.amount,
        )

        self.assertIsNone(
            self.state.issuance_record("issue-interrupted")
        )

        result = self.coordinator.issue(
            tx_id="issue-interrupted",
            recipient="account-A",
            stage_number=1,
            amount=self.amount,
            recorded_on=date(2026, 1, 2),
        )

        self.assertEqual(result.amount, self.amount)
        self.assertEqual(self.ledger.issued_supply, self.amount)
        self.assertEqual(self.state.issuance_total(), self.amount)

    def test_same_tx_id_with_different_request_is_rejected(self):
        self.coordinator.issue(
            tx_id="issue-mismatch",
            recipient="account-A",
            stage_number=1,
            amount=self.amount,
            recorded_on=date(2026, 1, 2),
        )

        with self.assertRaises(IssuanceCoordinatorError):
            self.coordinator.issue(
                tx_id="issue-mismatch",
                recipient="account-B",
                stage_number=1,
                amount=self.amount,
                recorded_on=date(2026, 1, 2),
            )

        self.assertEqual(self.ledger.balance_of("account-A"), self.amount)
        self.assertEqual(self.ledger.balance_of("account-B"), 0)

    def test_release_record_without_ledger_issuance_is_rejected(self):
        self.state.record_issuance(
            self.schedule,
            tx_id="state-only",
            stage_number=1,
            amount=self.amount,
            recorded_on=date(2026, 1, 2),
        )

        with self.assertRaises(IssuanceCoordinatorError):
            self.coordinator.issue(
                tx_id="state-only",
                recipient="account-A",
                stage_number=1,
                amount=self.amount,
                recorded_on=date(2026, 1, 2),
            )

        self.assertEqual(self.ledger.issued_supply, 0)

    def test_inactive_stage_is_rejected_before_ledger_mutation(self):
        with self.assertRaises(ReleaseStateError):
            self.coordinator.issue(
                tx_id="inactive-stage",
                recipient="account-A",
                stage_number=2,
                amount=self.amount,
                recorded_on=date(2026, 7, 1),
            )

        self.assertEqual(self.ledger.issued_supply, 0)
        self.assertIsNone(self.state.issuance_record("inactive-stage"))

    def test_existing_non_issuance_transaction_id_is_rejected(self):
        # Use a valid transaction ID already occupied by a ledger transfer.
        from financial_core.blockchain.native_ledger import Transfer

        self.ledger.issue_to(
            "funding-issuance",
            "funded-account",
            10000,
        )
        self.ledger.transfer(
            Transfer(
                tx_id="used-tx",
                sender="funded-account",
                recipient="other-account",
                amount=1,
            )
        )

        with self.assertRaises(DuplicateTransaction):
            self.coordinator.issue(
                tx_id="used-tx",
                recipient="account-A",
                stage_number=1,
                amount=self.amount,
                recorded_on=date(2026, 1, 2),
            )

        self.assertEqual(self.ledger.issued_supply, 10000)
        self.assertIsNone(self.state.issuance_record("used-tx"))


if __name__ == "__main__":
    unittest.main()
