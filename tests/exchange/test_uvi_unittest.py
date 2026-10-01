"""EX-009 Exchange -> UVI integration tests."""

import unittest

from financial_core.exchange.contracts import ExchangeRequest
from financial_core.exchange.executor import ExchangeExecutor
from platform_core.universal_value.core.contracts import ValueEvent
from platform_core.universal_value.ledger.value_ledger import ValueLedger
from platform_core.universal_value.transactions.transaction_manager import (
    TransactionManager,
)


class TestExchangeUVI(unittest.TestCase):

    def setUp(self):
        self.ledger = ValueLedger()
        self.transaction_manager = TransactionManager(self.ledger)

        seed_event = ValueEvent(
            event_id="SEED-POINT-001",
            user_id="USER-002",
            source="TEST",
            action="EARN",
            base_value=1000,
            currency="POINT",
            metadata={},
        )

        self.transaction_manager.create_transaction(
            event=seed_event,
            amount=1000,
            transaction_type="EARN",
        )

    def test_exchange_request_requires_uvi_conversion_fields(self):
        request = ExchangeRequest(
            operation_id="EX-UVI-001",
            user_id="USER-001",
            source_unit="POINT",
            target_unit="SHIR",
            source_amount="1000",
            quoted_target_amount="1",
            conversion_rate="0.001",
            fee_amount="0",
        )

        self.assertEqual(request.user_id, "USER-001")
        self.assertEqual(request.conversion_rate, "0.001")

    def test_exchange_executes_real_uvi_conversion(self):
        request = ExchangeRequest(
            operation_id="EX-UVI-002",
            user_id="USER-002",
            source_unit="POINT",
            target_unit="SHIR",
            source_amount="1000",
            quoted_target_amount="1",
            conversion_rate="0.001",
            fee_amount="0",
        )

        result = ExchangeExecutor(self.ledger).execute(request)

        self.assertEqual(result.operation_id, "EX-UVI-002")
        self.assertEqual(result.status, "READY_FOR_SETTLEMENT")
        self.assertIsNotNone(result.settlement_request)

        self.assertEqual(
            self.ledger.balance("USER-002", "POINT"),
            0,
        )
        self.assertEqual(
            self.ledger.balance("USER-002", "SHIR"),
            1,
        )

        entries = self.ledger.user_entries("USER-002")

        conversion_out = [
            entry
            for entry in entries
            if entry.transaction_type == "CONVERSION_OUT"
        ]

        conversion_in = [
            entry
            for entry in entries
            if entry.transaction_type == "CONVERSION_IN"
        ]

        self.assertEqual(len(conversion_out), 1)
        self.assertEqual(len(conversion_in), 1)

        self.assertEqual(conversion_out[0].currency, "POINT")
        self.assertEqual(conversion_out[0].amount, 1000)

        self.assertEqual(conversion_in[0].currency, "SHIR")
        self.assertEqual(conversion_in[0].amount, 1)


if __name__ == "__main__":
    unittest.main()
