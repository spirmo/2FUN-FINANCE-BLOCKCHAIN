"""EX-009 -> EX-010 Exchange to Settlement E2E test."""

import unittest

from financial_core.exchange.contracts import ExchangeRequest
from financial_core.exchange.executor import ExchangeExecutor
from financial_core.settlement.executor import SettlementExecutor
from platform_core.universal_value.ledger.value_ledger import ValueLedger


class TestExchangeToSettlementE2E(unittest.TestCase):

    def test_exchange_conversion_then_internal_settlement(self):
        ledger = ValueLedger()

        from decimal import Decimal

        ledger.record(
            transaction_id="INITIAL-001",
            event_id="INITIAL-EVENT-001",
            user_id="USER-001",
            amount=Decimal("1000"),
            currency="POINT",
            transaction_type="CREDIT",
            metadata={"source": "E2E_TEST"},
        )

        exchange_request = ExchangeRequest(
            operation_id="EX-SETTLE-001",
            user_id="USER-001",
            source_unit="POINT",
            target_unit="SHIR",
            source_amount="1000",
            quoted_target_amount="1",
            conversion_rate="0.001",
            fee_amount="0",
            metadata={
                "test": "EX-009-EX-010-E2E",
            },
        )

        exchange_result = ExchangeExecutor(ledger).execute(
            exchange_request
        )

        self.assertEqual(
            exchange_result.status,
            "READY_FOR_SETTLEMENT",
        )
        self.assertEqual(exchange_result.target_amount, "1")
        self.assertIsNotNone(exchange_result.settlement_request)

        settlement_result = SettlementExecutor().execute(
            exchange_result.settlement_request
        )

        self.assertEqual(
            settlement_result.operation_id,
            "EX-SETTLE-001",
        )
        self.assertEqual(
            settlement_result.settlement_type,
            "INTERNAL",
        )
        self.assertEqual(
            settlement_result.status,
            "SETTLED",
        )

        self.assertEqual(
            ledger.balance("USER-001", "POINT"),
            0,
        )
        self.assertEqual(
            ledger.balance("USER-001", "SHIR"),
            1,
        )


if __name__ == "__main__":
    unittest.main()
