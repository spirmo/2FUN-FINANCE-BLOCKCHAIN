import unittest

from financial_core.blockchain.fee_policy import FeePolicy
from financial_core.blockchain.native_ledger import (
    DuplicateTransaction,
    InsufficientBalance,
    LedgerError,
    NativeLedger,
    Transfer,
)
from financial_core.blockchain.twofunc_supply import (
    BASE_UNITS_PER_2FUNC,
    BASE_UNITS_PER_DRIKA,
    MAX_SUPPLY_BASE_UNITS,
)


class NativeLedgerTests(unittest.TestCase):
    def setUp(self):
        self.ledger = NativeLedger({
            "alice": 100 * BASE_UNITS_PER_2FUNC,
            "bob": 20 * BASE_UNITS_PER_2FUNC,
        })

    def make_fee_quote(self, operation_type="TRANSFER", resource_units=5):
        # Test-only rates; not production network rates.
        policy = FeePolicy(
            base_fee_drika={"TRANSFER": 10, "CONTRACT": 20},
            price_per_resource_unit_drika=2,
            max_fee_drika=100,
        )
        return policy.quote(
            operation_type=operation_type,
            resource_units=resource_units,
        )

    def test_transfer_moves_exact_base_units(self):
        amount = 30 * BASE_UNITS_PER_2FUNC
        self.ledger.transfer(Transfer("tx-1", "alice", "bob", amount))
        self.assertEqual(
            self.ledger.balance_of("alice"),
            70 * BASE_UNITS_PER_2FUNC,
        )
        self.assertEqual(
            self.ledger.balance_of("bob"),
            50 * BASE_UNITS_PER_2FUNC,
        )
        self.assertEqual(
            self.ledger.total_balances,
            120 * BASE_UNITS_PER_2FUNC,
        )

    def test_drika_transfer_uses_exact_conversion(self):
        self.ledger.transfer(
            Transfer.in_drika("tx-drika", "alice", "bob", 25)
        )
        self.assertEqual(
            self.ledger.balance_of("alice"),
            100 * BASE_UNITS_PER_2FUNC - 25 * BASE_UNITS_PER_DRIKA,
        )
        self.assertEqual(
            self.ledger.balance_of("bob"),
            20 * BASE_UNITS_PER_2FUNC + 25 * BASE_UNITS_PER_DRIKA,
        )

    def test_insufficient_balance_changes_nothing(self):
        with self.assertRaises(InsufficientBalance):
            self.ledger.transfer(
                Transfer("tx-2", "alice", "bob", 101 * BASE_UNITS_PER_2FUNC)
            )
        self.assertEqual(
            self.ledger.balance_of("alice"),
            100 * BASE_UNITS_PER_2FUNC,
        )
        self.assertEqual(
            self.ledger.balance_of("bob"),
            20 * BASE_UNITS_PER_2FUNC,
        )

    def test_duplicate_transaction_is_rejected(self):
        tx = Transfer("tx-3", "alice", "bob", 10 * BASE_UNITS_PER_2FUNC)
        self.ledger.transfer(tx)
        with self.assertRaises(DuplicateTransaction):
            self.ledger.transfer(tx)
        self.assertEqual(
            self.ledger.balance_of("alice"),
            90 * BASE_UNITS_PER_2FUNC,
        )
        self.assertEqual(
            self.ledger.balance_of("bob"),
            30 * BASE_UNITS_PER_2FUNC,
        )

    def test_zero_and_negative_amounts_are_rejected(self):
        for amount in (0, -1):
            with self.subTest(amount=amount):
                with self.assertRaises(LedgerError):
                    self.ledger.transfer(
                        Transfer(f"tx-{amount}", "alice", "bob", amount)
                    )

    def test_sender_cannot_transfer_to_self(self):
        with self.assertRaises(LedgerError):
            self.ledger.transfer(
                Transfer("tx-self", "alice", "alice", 10)
            )

    def test_unknown_account_has_zero_balance(self):
        self.assertEqual(self.ledger.balance_of("unknown"), 0)

    def test_initial_balances_cannot_exceed_supply(self):
        with self.assertRaises(LedgerError):
            NativeLedger({"alice": MAX_SUPPLY_BASE_UNITS + 1})

    def test_invalid_initial_balance_is_rejected(self):
        with self.assertRaises(LedgerError):
            NativeLedger({"alice": -1})

    def test_failed_transfer_does_not_consume_transaction_id(self):
        tx = Transfer(
            "tx-retry", "alice", "bob", 101 * BASE_UNITS_PER_2FUNC
        )
        with self.assertRaises(InsufficientBalance):
            self.ledger.transfer(tx)

        self.ledger.transfer(
            Transfer("tx-retry", "alice", "bob", 10 * BASE_UNITS_PER_2FUNC)
        )
        self.assertEqual(
            self.ledger.balance_of("alice"),
            90 * BASE_UNITS_PER_2FUNC,
        )

    def test_transfer_and_fee_are_recorded_together(self):
        tx = Transfer.in_drika(
            "tx-with-fee", "alice", "bob", 100
        )
        quote = self.make_fee_quote()
        before_total = self.ledger.total_balances

        self.ledger.transfer_with_fee(
            tx,
            fee_quote=quote,
            fee_recipient="treasury",
        )

        self.assertEqual(
            self.ledger.balance_of("alice"),
            100 * BASE_UNITS_PER_2FUNC
            - 100 * BASE_UNITS_PER_DRIKA
            - quote.fee_base_units,
        )
        self.assertEqual(
            self.ledger.balance_of("bob"),
            20 * BASE_UNITS_PER_2FUNC
            + 100 * BASE_UNITS_PER_DRIKA,
        )
        self.assertEqual(
            self.ledger.balance_of("treasury"),
            quote.fee_base_units,
        )
        self.assertEqual(self.ledger.total_balances, before_total)

        payment = self.ledger.fee_payment_for("tx-with-fee")
        self.assertIsNotNone(payment)
        self.assertEqual(payment.fee_drika, quote.fee_drika)
        self.assertEqual(payment.payer, "alice")
        self.assertEqual(payment.fee_recipient, "treasury")
        self.assertTrue(self.ledger.transaction_exists("tx-with-fee"))

    def test_fee_and_transfer_fail_together_if_combined_balance_is_insufficient(self):
        quote = self.make_fee_quote()
        tx = Transfer(
            "tx-combined-insufficient",
            "alice",
            "bob",
            100 * BASE_UNITS_PER_2FUNC,
        )
        before = {
            account: self.ledger.balance_of(account)
            for account in ("alice", "bob", "treasury")
        }
        before_total = self.ledger.total_balances

        with self.assertRaises(InsufficientBalance):
            self.ledger.transfer_with_fee(
                tx,
                fee_quote=quote,
                fee_recipient="treasury",
            )

        self.assertEqual(
            {
                account: self.ledger.balance_of(account)
                for account in ("alice", "bob", "treasury")
            },
            before,
        )
        self.assertEqual(self.ledger.total_balances, before_total)
        self.assertFalse(
            self.ledger.transaction_exists("tx-combined-insufficient")
        )
        self.assertIsNone(
            self.ledger.fee_payment_for("tx-combined-insufficient")
        )

    def test_failed_fee_transfer_does_not_consume_transaction_id(self):
        quote = self.make_fee_quote()
        too_large = Transfer(
            "tx-fee-retry",
            "alice",
            "bob",
            100 * BASE_UNITS_PER_2FUNC,
        )

        with self.assertRaises(InsufficientBalance):
            self.ledger.transfer_with_fee(
                too_large,
                fee_quote=quote,
                fee_recipient="treasury",
            )

        retry = Transfer.in_drika(
            "tx-fee-retry", "alice", "bob", 10
        )
        self.ledger.transfer_with_fee(
            retry,
            fee_quote=quote,
            fee_recipient="treasury",
        )

        self.assertTrue(self.ledger.transaction_exists("tx-fee-retry"))
        self.assertIsNotNone(self.ledger.fee_payment_for("tx-fee-retry"))

    def test_fee_cannot_be_charged_twice_for_same_transaction(self):
        tx = Transfer.in_drika("tx-fee-duplicate", "alice", "bob", 10)
        quote = self.make_fee_quote()

        self.ledger.transfer_with_fee(
            tx,
            fee_quote=quote,
            fee_recipient="treasury",
        )
        after_first_charge = self.ledger.balance_of("treasury")

        with self.assertRaises(DuplicateTransaction):
            self.ledger.transfer_with_fee(
                tx,
                fee_quote=quote,
                fee_recipient="treasury",
            )

        self.assertEqual(
            self.ledger.balance_of("treasury"),
            after_first_charge,
        )

    def test_invalid_fee_conversion_is_rejected_without_mutation(self):
        quote = self.make_fee_quote()
        forged_quote = type(quote)(
            operation_type=quote.operation_type,
            resource_units=quote.resource_units,
            fee_drika=quote.fee_drika,
            fee_base_units=quote.fee_base_units + 1,
        )
        tx = Transfer.in_drika(
            "tx-invalid-fee", "alice", "bob", 10
        )
        before_alice = self.ledger.balance_of("alice")
        before_bob = self.ledger.balance_of("bob")

        with self.assertRaises(LedgerError):
            self.ledger.transfer_with_fee(
                tx,
                fee_quote=forged_quote,
                fee_recipient="treasury",
            )

        self.assertEqual(self.ledger.balance_of("alice"), before_alice)
        self.assertEqual(self.ledger.balance_of("bob"), before_bob)
        self.assertFalse(self.ledger.transaction_exists("tx-invalid-fee"))

    def test_fee_recipient_must_be_distinct(self):
        tx = Transfer.in_drika(
            "tx-fee-recipient", "alice", "bob", 10
        )
        quote = self.make_fee_quote()

        with self.assertRaises(LedgerError):
            self.ledger.transfer_with_fee(
                tx,
                fee_quote=quote,
                fee_recipient="bob",
            )

        self.assertFalse(self.ledger.transaction_exists("tx-fee-recipient"))

    def test_fee_payment_for_unknown_transaction_is_none(self):
        self.assertIsNone(self.ledger.fee_payment_for("missing"))


if __name__ == "__main__":
    unittest.main()
