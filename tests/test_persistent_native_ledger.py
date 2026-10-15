import os
import tempfile
import unittest

from financial_core.blockchain.fee_policy import FeePolicy
from financial_core.blockchain.native_ledger import (
    DuplicateTransaction,
    Transfer,
)
from financial_core.blockchain.persistent_native_ledger import (
    SQLiteNativeLedger,
)
from financial_core.blockchain.twofunc_supply import BASE_UNITS_PER_2FUNC


class PersistentNativeLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "twofunc.sqlite3")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_issuance_and_balances_survive_restart(self):
        ledger = SQLiteNativeLedger(self.db_path)
        amount = 7 * BASE_UNITS_PER_2FUNC
        ledger.issue_to("ISSUE-1", "alice", amount)
        ledger.close()

        reopened = SQLiteNativeLedger(self.db_path)
        try:
            self.assertEqual(reopened.balance_of("alice"), amount)
            self.assertEqual(reopened.issued_supply, amount)
            self.assertEqual(reopened.issuance_for("ISSUE-1").amount, amount)
            with self.assertRaises(DuplicateTransaction):
                reopened.issue_to("ISSUE-1", "alice", amount)
        finally:
            reopened.close()

    def test_transfer_and_duplicate_protection_survive_restart(self):
        initial = {"alice": 100, "bob": 20}
        ledger = SQLiteNativeLedger(self.db_path, initial)
        ledger.transfer(Transfer("TX-1", "alice", "bob", 30))
        ledger.close()

        reopened = SQLiteNativeLedger(self.db_path)
        try:
            self.assertEqual(reopened.balance_of("alice"), 70)
            self.assertEqual(reopened.balance_of("bob"), 50)
            self.assertEqual(reopened.issued_supply, 120)
            with self.assertRaises(DuplicateTransaction):
                reopened.transfer(Transfer("TX-1", "alice", "bob", 30))
        finally:
            reopened.close()

    def test_fee_record_survives_restart(self):
        policy = FeePolicy(
            base_fee_drika={"TRANSFER": 1},
            price_per_resource_unit_drika=0,
            max_fee_drika=10,
        )
        quote = policy.quote("TRANSFER", 0)
        ledger = SQLiteNativeLedger(self.db_path, {"alice": 1000, "bob": 0})
        ledger.transfer_with_fee(
            Transfer("TX-FEE", "alice", "bob", 100),
            fee_quote=quote,
            fee_recipient="treasury",
        )
        ledger.close()

        reopened = SQLiteNativeLedger(self.db_path)
        try:
            payment = reopened.fee_payment_for("TX-FEE")
            self.assertIsNotNone(payment)
            self.assertEqual(payment.payer, "alice")
            self.assertEqual(payment.fee_recipient, "treasury")
            self.assertEqual(reopened.total_balances, 1000)
        finally:
            reopened.close()

    def test_existing_database_ignores_new_initial_balances(self):
        ledger = SQLiteNativeLedger(self.db_path, {"alice": 100})
        ledger.close()

        reopened = SQLiteNativeLedger(self.db_path, {"mallory": 999})
        try:
            self.assertEqual(reopened.balance_of("alice"), 100)
            self.assertEqual(reopened.balance_of("mallory"), 0)
        finally:
            reopened.close()


if __name__ == "__main__":
    unittest.main()
