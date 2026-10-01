"""EX-010 Settlement execution tests."""

import unittest

from financial_core.settlement.contracts import SettlementRequest
from financial_core.settlement.executor import SettlementExecutor


class TestSettlementExecutor(unittest.TestCase):

    def test_internal_settlement_produces_settled_record(self):
        request = SettlementRequest(
            operation_id="SETTLE-001",
            settlement_type="INTERNAL",
            amount="1000",
            unit="POINT",
            metadata={
                "settlement_source": "EXCHANGE",
                "exchange_target_unit": "SHIR",
                "exchange_target_amount": "1",
            },
        )

        record = SettlementExecutor().execute(request)

        self.assertEqual(record.operation_id, "SETTLE-001")
        self.assertEqual(record.settlement_type, "INTERNAL")
        self.assertEqual(record.amount, "1000")
        self.assertEqual(record.unit, "POINT")
        self.assertEqual(record.status, "SETTLED")
        self.assertIsNone(record.transaction_reference)

        self.assertEqual(
            record.metadata["settlement_source"],
            "EXCHANGE",
        )
        self.assertEqual(
            record.metadata["exchange_target_unit"],
            "SHIR",
        )
        self.assertEqual(
            record.metadata["exchange_target_amount"],
            "1",
        )

    def test_invalid_internal_settlement_is_rejected(self):
        request = SettlementRequest(
            operation_id="SETTLE-002",
            settlement_type="INTERNAL",
            amount="0",
            unit="POINT",
        )

        with self.assertRaises(ValueError):
            SettlementExecutor().execute(request)


if __name__ == "__main__":
    unittest.main()
