"""EX-011 Internal transfer executor tests."""

import unittest
from decimal import Decimal

from financial_core.internal.contracts import InternalTransferRequest
from financial_core.internal.executor import InternalTransferExecutor
from platform_core.universal_value.ledger.value_ledger import ValueLedger


class TestInternalTransferExecutor(unittest.TestCase):

    def test_internal_transfer_moves_value_between_users(self):
        ledger = ValueLedger()

        ledger.record(
            transaction_id="INITIAL-INT-001",
            event_id="INITIAL-EVENT-INT-001",
            user_id="USER-001",
            amount=Decimal("100"),
            currency="POINT",
            transaction_type="CREDIT",
            metadata={"source": "E2E_TEST"},
        )

        request = InternalTransferRequest(
            operation_id="INT-001",
            source_user_id="USER-001",
            target_user_id="USER-002",
            amount="40",
            unit="POINT",
            metadata={"test": "EX-011"},
        )

        record = InternalTransferExecutor(ledger).execute(request)

        self.assertEqual(record.operation_id, "INT-001")
        self.assertEqual(record.source_user_id, "USER-001")
        self.assertEqual(record.target_user_id, "USER-002")
        self.assertEqual(record.amount, "40")
        self.assertEqual(record.unit, "POINT")
        self.assertEqual(record.status, "TRANSFERRED")

        self.assertIsNotNone(record.source_transaction_id)
        self.assertIsNotNone(record.target_transaction_id)

        self.assertEqual(
            ledger.balance("USER-001", "POINT"),
            Decimal("60"),
        )
        self.assertEqual(
            ledger.balance("USER-002", "POINT"),
            Decimal("40"),
        )

        entries = ledger.all_entries()
        self.assertEqual(len(entries), 3)

        self.assertEqual(
            entries[1].transaction_type,
            "SPEND",
        )
        self.assertEqual(
            entries[2].transaction_type,
            "CREDIT",
        )

    def test_insufficient_balance_is_rejected(self):
        ledger = ValueLedger()

        ledger.record(
            transaction_id="INITIAL-INT-002",
            event_id="INITIAL-EVENT-INT-002",
            user_id="USER-001",
            amount=Decimal("10"),
            currency="POINT",
            transaction_type="CREDIT",
        )

        request = InternalTransferRequest(
            operation_id="INT-002",
            source_user_id="USER-001",
            target_user_id="USER-002",
            amount="20",
            unit="POINT",
        )

        with self.assertRaises(ValueError):
            InternalTransferExecutor(ledger).execute(request)

        self.assertEqual(
            ledger.balance("USER-001", "POINT"),
            Decimal("10"),
        )
        self.assertEqual(
            ledger.balance("USER-002", "POINT"),
            Decimal("0"),
        )


if __name__ == "__main__":
    unittest.main()
