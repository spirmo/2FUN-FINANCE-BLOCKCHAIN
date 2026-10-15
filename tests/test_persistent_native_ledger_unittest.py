"""Persistence tests for the SQLite-backed native 2FUNC ledger."""

import os
import tempfile
import unittest

from financial_core.blockchain.fee_policy import FeePolicy
from financial_core.blockchain.native_ledger import (
    DuplicateTransaction,
    LedgerError,
    Transfer,
)
from financial_core.blockchain.persistent_native_ledger import (
    SQLiteNativeLedger,
)
from financial_core.blockchain.twofunc_supply import (
    drika_to_base_units,
)


class PersistentNativeLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(
            self.temp_dir.name,
            "twofunc_ledger.sqlite3",
        )
        self.ledger = SQLiteNativeLedger(
            self.db_path,
            initial_balances={
                "alice": drika_to_base_units(100),
            },
        )

    def tearDown(self):
        if getattr(self, "ledger", None) is not None:
            self.ledger.close()
        self.temp_dir.cleanup()

    def reopen(self):
        self.ledger.close()
        self.ledger = SQLiteNativeLedger(self.db_path)

    def test_initial_balances_survive_restart(self):
        expected = drika_to_base_units(100)

        self.reopen()

        self.assertEqual(self.ledger.balance_of("alice"), expected)
        self.assertEqual(self.ledger.issued_supply, expected)
        self.assertEqual(self.ledger.total_balances, expected)

    def test_issuance_survives_restart(self):
        amount = drika_to_base_units(5)

        record = self.ledger.issue_to(
            "issue-001",
            "bob",
            amount,
        )

        self.reopen()

        self.assertEqual(self.ledger.balance_of("bob"), amount)
        self.assertEqual(self.ledger.issuance_for("issue-001"), record)
        self.assertEqual(
            self.ledger.issued_supply,
            drika_to_base_units(105),
        )

    def test_duplicate_issuance_is_rejected_after_restart(self):
        amount = drika_to_base_units(5)
        self.ledger.issue_to("issue-002", "bob", amount)

        self.reopen()

        with self.assertRaises(DuplicateTransaction):
            self.ledger.issue_to("issue-002", "carol", amount)

        self.assertEqual(self.ledger.balance_of("carol"), 0)
        self.assertEqual(self.ledger.balance_of("bob"), amount)

    def test_transfer_survives_restart(self):
        tx = Transfer(
            "transfer-001",
            "alice",
            "bob",
            drika_to_base_units(20),
        )
        self.ledger.transfer(tx)

        self.reopen()

        self.assertEqual(
            self.ledger.balance_of("alice"),
            drika_to_base_units(80),
        )
        self.assertEqual(
            self.ledger.balance_of("bob"),
            drika_to_base_units(20),
        )
        self.assertTrue(self.ledger.transaction_exists("transfer-001"))

    def test_duplicate_transfer_is_rejected_after_restart(self):
        tx = Transfer(
            "transfer-002",
            "alice",
            "bob",
            drika_to_base_units(10),
        )
        self.ledger.transfer(tx)

        self.reopen()

        with self.assertRaises(DuplicateTransaction):
            self.ledger.transfer(tx)

        self.assertEqual(
            self.ledger.balance_of("alice"),
            drika_to_base_units(90),
        )
        self.assertEqual(
            self.ledger.balance_of("bob"),
            drika_to_base_units(10),
        )

    def test_fee_payment_survives_restart(self):
        quote = FeePolicy(
            base_fee_drika={"TRANSFER": 2},
            price_per_resource_unit_drika=1,
            max_fee_drika=100,
        ).quote(
            operation_type="TRANSFER",
            resource_units=3,
        )

        tx = Transfer(
            "fee-transfer-001",
            "alice",
            "bob",
            drika_to_base_units(10),
        )

        self.ledger.transfer_with_fee(
            tx,
            fee_quote=quote,
            fee_recipient="network",
        )

        self.reopen()

        self.assertEqual(
            self.ledger.balance_of("alice"),
            drika_to_base_units(100)
            - drika_to_base_units(10)
            - quote.fee_base_units,
        )
        self.assertEqual(
            self.ledger.balance_of("bob"),
            drika_to_base_units(10),
        )
        self.assertEqual(
            self.ledger.balance_of("network"),
            quote.fee_base_units,
        )

        payment = self.ledger.fee_payment_for("fee-transfer-001")
        self.assertIsNotNone(payment)
        self.assertEqual(payment.payer, "alice")
        self.assertEqual(payment.fee_recipient, "network")
        self.assertEqual(payment.fee_drika, 5)
        self.assertEqual(payment.fee_base_units, quote.fee_base_units)

    def test_issuance_and_transfer_cannot_reuse_transaction_id(self):
        amount = drika_to_base_units(5)
        self.ledger.issue_to("shared-id", "bob", amount)

        with self.assertRaises(DuplicateTransaction):
            self.ledger.transfer(
                Transfer(
                    "shared-id",
                    "alice",
                    "carol",
                    drika_to_base_units(1),
                )
            )

        self.assertEqual(self.ledger.balance_of("carol"), 0)

    def test_failed_transfer_does_not_change_persisted_state(self):
        before = self.ledger.balance_of("alice")

        with self.assertRaises(LedgerError):
            self.ledger.transfer(
                Transfer(
                    "invalid-transfer",
                    "alice",
                    "bob",
                    drika_to_base_units(200),
                )
            )

        self.reopen()

        self.assertEqual(self.ledger.balance_of("alice"), before)
        self.assertEqual(self.ledger.balance_of("bob"), 0)
        self.assertFalse(
            self.ledger.transaction_exists("invalid-transfer")
        )


    def test_multiple_instances_do_not_lose_persisted_transfers(self):
        second = SQLiteNativeLedger(self.db_path)

        try:
            first_tx = Transfer(
                "instance-one-transfer",
                "alice",
                "bob",
                drika_to_base_units(10),
            )
            second_tx = Transfer(
                "instance-two-transfer",
                "alice",
                "carol",
                drika_to_base_units(5),
            )

            self.ledger.transfer(first_tx)
            second.transfer(second_tx)
        finally:
            second.close()

        self.reopen()

        self.assertEqual(
            self.ledger.balance_of("alice"),
            drika_to_base_units(85),
        )
        self.assertEqual(
            self.ledger.balance_of("bob"),
            drika_to_base_units(10),
        )
        self.assertEqual(
            self.ledger.balance_of("carol"),
            drika_to_base_units(5),
        )
        self.assertTrue(
            self.ledger.transaction_exists("instance-one-transfer")
        )
        self.assertTrue(
            self.ledger.transaction_exists("instance-two-transfer")
        )

    def test_persistence_failure_rolls_back_memory_and_database(self):
        import sqlite3

        alice_before = self.ledger.balance_of("alice")
        bob_before = self.ledger.balance_of("bob")
        supply_before = self.ledger.issued_supply

        self.ledger._db.execute("""
            CREATE TRIGGER force_transfer_persistence_failure
            BEFORE INSERT ON ledger_transfers
            WHEN NEW.tx_id = 'forced-persistence-failure'
            BEGIN
                SELECT RAISE(ABORT, 'forced persistence failure');
            END
        """)
        self.ledger._db.commit()

        tx = Transfer(
            "forced-persistence-failure",
            "alice",
            "bob",
            drika_to_base_units(10),
        )

        with self.assertRaises(sqlite3.IntegrityError):
            self.ledger.transfer(tx)

        self.assertEqual(self.ledger.balance_of("alice"), alice_before)
        self.assertEqual(self.ledger.balance_of("bob"), bob_before)
        self.assertEqual(self.ledger.issued_supply, supply_before)
        self.assertFalse(
            self.ledger.transaction_exists("forced-persistence-failure")
        )

        self.reopen()

        self.assertEqual(self.ledger.balance_of("alice"), alice_before)
        self.assertEqual(self.ledger.balance_of("bob"), bob_before)
        self.assertEqual(self.ledger.issued_supply, supply_before)
        self.assertFalse(
            self.ledger.transaction_exists("forced-persistence-failure")
        )

    def test_issuance_and_transfer_share_duplicate_id_protection(self):
        self.ledger.transfer(
            Transfer(
                "shared-transfer-id",
                "alice",
                "bob",
                drika_to_base_units(1),
            )
        )

        self.reopen()

        with self.assertRaises(DuplicateTransaction):
            self.ledger.issue_to(
                "shared-transfer-id",
                "carol",
                drika_to_base_units(1),
            )

        self.assertEqual(self.ledger.balance_of("carol"), 0)


if __name__ == "__main__":
    unittest.main()
