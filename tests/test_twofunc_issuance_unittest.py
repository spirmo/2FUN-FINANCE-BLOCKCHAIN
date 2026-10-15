import unittest

from financial_core.blockchain.native_ledger import (
    DuplicateTransaction,
    LedgerError,
    NativeLedger,
)
from financial_core.blockchain.twofunc_supply import (
    BASE_UNITS_PER_2FUNC,
    MAX_SUPPLY_BASE_UNITS,
)


class TestNativeTwoFuncIssuance(unittest.TestCase):
    def test_successful_issuance_updates_balance_and_supply(self):
        ledger = NativeLedger()
        amount = 7 * BASE_UNITS_PER_2FUNC

        record = ledger.issue_to("ISSUE-001", "alice", amount)

        self.assertEqual(record.tx_id, "ISSUE-001")
        self.assertEqual(record.recipient, "alice")
        self.assertEqual(record.amount, amount)
        self.assertEqual(ledger.balance_of("alice"), amount)
        self.assertEqual(ledger.issued_supply, amount)
        self.assertEqual(ledger.total_balances, amount)
        self.assertEqual(
            ledger.remaining_supply,
            MAX_SUPPLY_BASE_UNITS - amount,
        )
        self.assertEqual(ledger.issuance_for("ISSUE-001"), record)
        self.assertTrue(ledger.transaction_exists("ISSUE-001"))

    def test_initial_balances_count_as_issued_supply(self):
        initial = {"genesis": 3 * BASE_UNITS_PER_2FUNC}
        ledger = NativeLedger(initial)

        self.assertEqual(ledger.issued_supply, sum(initial.values()))
        self.assertEqual(ledger.total_balances, ledger.issued_supply)

    def test_issuance_cannot_exceed_supply_cap(self):
        ledger = NativeLedger({"genesis": MAX_SUPPLY_BASE_UNITS})
        before = (ledger.balance_of("genesis"), ledger.issued_supply)

        with self.assertRaises(LedgerError):
            ledger.issue_to("ISSUE-002", "alice", 1)

        self.assertEqual(
            (ledger.balance_of("genesis"), ledger.issued_supply),
            before,
        )
        self.assertIsNone(ledger.issuance_for("ISSUE-002"))

    def test_duplicate_issuance_id_is_rejected_atomically(self):
        ledger = NativeLedger()
        ledger.issue_to("ISSUE-003", "alice", 10)
        before = (ledger.balance_of("alice"), ledger.issued_supply)

        with self.assertRaises(DuplicateTransaction):
            ledger.issue_to("ISSUE-003", "alice", 20)

        self.assertEqual(
            (ledger.balance_of("alice"), ledger.issued_supply),
            before,
        )

    def test_issuance_id_cannot_reuse_transfer_id(self):
        ledger = NativeLedger({"alice": 100})
        from financial_core.blockchain.native_ledger import Transfer

        ledger.transfer(Transfer("SHARED-ID", "alice", "bob", 10))

        with self.assertRaises(DuplicateTransaction):
            ledger.issue_to("SHARED-ID", "bob", 5)

        self.assertEqual(ledger.balance_of("bob"), 10)
        self.assertEqual(ledger.issued_supply, 100)

    def test_invalid_issuance_does_not_change_state(self):
        ledger = NativeLedger()
        for tx_id, recipient, amount in (
            ("", "alice", 1),
            ("ISSUE-004", "", 1),
            ("ISSUE-005", "alice", 0),
            ("ISSUE-006", "alice", -1),
            ("ISSUE-007", "alice", True),
            ("ISSUE-008", "alice", 1.5),
        ):
            before = (ledger.total_balances, ledger.issued_supply)
            with self.subTest(tx_id=tx_id, amount=amount):
                with self.assertRaises(LedgerError):
                    ledger.issue_to(tx_id, recipient, amount)
                self.assertEqual(
                    (ledger.total_balances, ledger.issued_supply),
                    before,
                )

    def test_transfer_does_not_increase_issued_supply(self):
        from financial_core.blockchain.native_ledger import Transfer

        ledger = NativeLedger({"alice": 100})
        ledger.transfer(Transfer("TRANSFER-001", "alice", "bob", 25))

        self.assertEqual(ledger.issued_supply, 100)
        self.assertEqual(ledger.total_balances, 100)
        self.assertEqual(ledger.balance_of("bob"), 25)


if __name__ == "__main__":
    unittest.main()
