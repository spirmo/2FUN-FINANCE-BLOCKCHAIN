import unittest
from decimal import Decimal

from financial_core.exchange.order import Order
from financial_core.exchange.order_types import OrderType, TimeInForce
from financial_core.exchange.contracts import ExchangeRequest
from financial_core.exchange.pipeline import ExchangePipeline
from platform_core.universal_value.ledger.value_ledger import ValueLedger


class TestExchangePipeline(unittest.TestCase):
    def _pipeline_with_uvi(self, user_id="USER-EX017"):
        ledger = ValueLedger()
        ledger.record(
            transaction_id=f"{user_id}:INITIAL",
            event_id=f"{user_id}:INITIAL-EVENT",
            user_id=user_id,
            amount=Decimal("1000"),
            currency="POINT",
            transaction_type="CREDIT",
            metadata={"stage": "EX-017"},
        )
        return ExchangePipeline(
            fee_rate="0.0025",
            uvi_ledger=ledger,
        ), ledger


    def test_buy_sell_to_trade_and_fee(self):
        pipeline, _ledger = self._pipeline_with_uvi("USER-EX017-MARKET")

        buy_order = Order(
            order_id="BUY-EX017-001",
            market_id="2FUNC-SHIR",
            account_id="BUYER-001",
            side="BUY",
            order_type=OrderType.LIMIT,
            quantity=Decimal("5"),
            price=Decimal("20"),
            status="OPEN",
            time_in_force=TimeInForce.GTC,
        )

        sell_order = Order(
            order_id="SELL-EX017-001",
            market_id="2FUNC-SHIR",
            account_id="SELLER-001",
            side="SELL",
            order_type=OrderType.LIMIT,
            quantity=Decimal("5"),
            price=Decimal("20"),
            status="OPEN",
            time_in_force=TimeInForce.GTC,
        )

        result = pipeline.execute_market(
            buy_order,
            sell_order,
        )

        self.assertEqual(
            result.trade.quantity,
            Decimal("5"),
        )

        self.assertEqual(
            result.trade.price,
            Decimal("20"),
        )

        self.assertEqual(
            result.trade.notional,
            Decimal("100"),
        )

        self.assertEqual(
            result.fee.fee_amount,
            Decimal("0.2500"),
        )


    def test_pipeline_can_execute_existing_uvi_conversion(self):
        from financial_core.contracts.uvi import UVIValueRequest
        from financial_core.integrations.uvi_exchange_adapter import UVIExchangeAdapter
        from platform_core.universal_value.ledger.value_ledger import ValueLedger

        ledger = ValueLedger()
        ledger.record(
            transaction_id="EX017-UVI-INITIAL",
            event_id="EX017-UVI-INITIAL-EVENT",
            user_id="USER-EX017-UVI",
            amount=Decimal("1000"),
            currency="POINT",
            transaction_type="CREDIT",
            metadata={"stage": "EX-017", "purpose": "test_initial_balance"},
        )

        adapter = UVIExchangeAdapter(ledger)

        result = adapter.process(
            UVIValueRequest(
                operation_id="EX017-UVI-001",
                user_id="USER-EX017-UVI",
                unit="POINT",
                amount="1000",
                metadata={"stage": "EX-017"},
            ),
            target_unit="SHIR",
            quoted_target_amount="1",
            conversion_rate="0.001",
        )

        self.assertEqual(result.status, "RECORDED")
        self.assertTrue(result.recorded)
        self.assertEqual(result.metadata["authority"], "EXISTING_UVI")
        self.assertEqual(
            result.metadata["source_amount"],
            "1000",
        )
        self.assertEqual(
            Decimal(result.metadata["target_amount"]),
            Decimal("1"),
        )
        self.assertEqual(
            ledger.balance("USER-EX017-UVI", "POINT"),
            Decimal("0"),
        )
        self.assertEqual(
            ledger.balance("USER-EX017-UVI", "SHIR"),
            Decimal("1"),
        )

    def test_duplicate_operation_id_is_rejected(self):
        from financial_core.exchange.contracts import ExchangeRequest

        request = ExchangeRequest(
            operation_id="EX017-DUP-001",
            user_id="USER-EX017",
            source_unit="POINT",
            target_unit="SHIR",
            source_amount="1000",
            quoted_target_amount="1",
            conversion_rate="0.001",
            fee_amount="0",
        )

        pipeline, _ledger = self._pipeline_with_uvi("USER-EX017")

        buy_order = Order(
            order_id="BUY-EX017-DUP-001",
            market_id="2FUNC-SHIR",
            account_id="BUYER-EX017",
            side="BUY",
            order_type=OrderType.LIMIT,
            quantity=Decimal("5"),
            price=Decimal("20"),
            status="OPEN",
            time_in_force=TimeInForce.GTC,
        )

        sell_order = Order(
            order_id="SELL-EX017-DUP-001",
            market_id="2FUNC-SHIR",
            account_id="SELLER-EX017",
            side="SELL",
            order_type=OrderType.LIMIT,
            quantity=Decimal("5"),
            price=Decimal("20"),
            status="OPEN",
            time_in_force=TimeInForce.GTC,
        )

        pipeline.execute(request, buy_order, sell_order)

        with self.assertRaisesRegex(ValueError, "operation already processed"):
            pipeline.execute(request, buy_order, sell_order)

    def test_pipeline_settles_uvi_result(self):
        pipeline, ledger = self._pipeline_with_uvi("USER-EX017-SETTLEMENT")

        request = ExchangeRequest(
            operation_id="EX017-SETTLEMENT-001",
            user_id="USER-EX017-SETTLEMENT",
            source_unit="POINT",
            target_unit="SHIR",
            source_amount="1000",
            quoted_target_amount="1",
            conversion_rate="0.001",
            metadata={"stage": "EX-017-009"},
        )

        buy_order = Order(
            order_id="BUY-EX017-SETTLEMENT",
            market_id="POINT-SHIR",
            account_id="BUYER",
            side="BUY",
            quantity="1",
            price="1",
            order_type="LIMIT",
        )
        sell_order = Order(
            order_id="SELL-EX017-SETTLEMENT",
            market_id="POINT-SHIR",
            account_id="SELLER",
            side="SELL",
            quantity="1",
            price="1",
            order_type="LIMIT",
        )

        result = pipeline.execute(
            request=request,
            buy_order=buy_order,
            sell_order=sell_order,
        )

        self.assertIsNotNone(result.uvi_result)
        self.assertTrue(result.uvi_result.recorded)

        self.assertIsNotNone(result.settlement_record)
        self.assertEqual(result.settlement_record.status, "SETTLED")
        self.assertEqual(result.settlement_record.operation_id, request.operation_id)
        self.assertEqual(result.settlement_record.amount, "1.000000000000000000")
        self.assertEqual(result.settlement_record.unit, "SHIR")
        self.assertEqual(
            result.settlement_record.metadata["settlement_mode"],
            "INTERNAL",
        )

    def test_pipeline_reconciles_settlement(self):
        pipeline, ledger = self._pipeline_with_uvi("USER-EX017-RECON")

        request = ExchangeRequest(
            operation_id="EX017-RECON-001",
            user_id="USER-EX017-RECON",
            source_unit="POINT",
            target_unit="SHIR",
            source_amount="1000",
            quoted_target_amount="1",
            conversion_rate="0.001",
            metadata={"stage": "EX-017-010"},
        )

        buy_order = Order(
            order_id="BUY-EX017-RECON",
            market_id="POINT-SHIR",
            account_id="BUYER",
            side="BUY",
            quantity="1",
            price="1",
            order_type="LIMIT",
        )
        sell_order = Order(
            order_id="SELL-EX017-RECON",
            market_id="POINT-SHIR",
            account_id="SELLER",
            side="SELL",
            quantity="1",
            price="1",
            order_type="LIMIT",
        )

        result = pipeline.execute(
            request=request,
            buy_order=buy_order,
            sell_order=sell_order,
        )

        self.assertIsNotNone(result.settlement_record)
        self.assertEqual(result.settlement_record.status, "SETTLED")

        self.assertIsNotNone(result.reconciliation_decision)
        self.assertEqual(
            result.reconciliation_decision.operation_id,
            request.operation_id,
        )
        self.assertEqual(
            result.reconciliation_decision.status,
            "MATCHED",
        )
        self.assertEqual(
            result.reconciliation_decision.difference,
            "0",
        )

    def test_full_exchange_execution_pipeline(self):
        pipeline, ledger = self._pipeline_with_uvi("USER-EX017-FINAL")

        request = ExchangeRequest(
            operation_id="EX017-FINAL-E2E-001",
            user_id="USER-EX017-FINAL",
            source_unit="POINT",
            target_unit="SHIR",
            source_amount="1000",
            quoted_target_amount="1",
            conversion_rate="0.001",
            metadata={"stage": "EX-017-011", "test": "final_e2e"},
        )

        buy_order = Order(
            order_id="BUY-EX017-FINAL",
            market_id="POINT-SHIR",
            account_id="BUYER",
            side="BUY",
            quantity="1",
            price="1",
            order_type="LIMIT",
        )

        sell_order = Order(
            order_id="SELL-EX017-FINAL",
            market_id="POINT-SHIR",
            account_id="SELLER",
            side="SELL",
            quantity="1",
            price="1",
            order_type="LIMIT",
        )

        result = pipeline.execute(
            request=request,
            buy_order=buy_order,
            sell_order=sell_order,
        )

        # Market execution
        self.assertEqual(result.trade.market_id, "POINT-SHIR")
        self.assertEqual(result.trade.quantity, Decimal("1"))
        self.assertEqual(result.trade.price, Decimal("1"))

        # Fee
        self.assertEqual(result.fee.trade_id, result.trade.trade_id)
        self.assertEqual(result.fee.fee_amount, Decimal("0.0025"))

        # Risk
        self.assertIsNotNone(result.risk_decision)
        self.assertTrue(result.risk_decision.approved)

        # Idempotency
        self.assertIsNotNone(result.idempotency_decision)
        self.assertTrue(result.idempotency_decision.accepted)

        # UVI
        self.assertIsNotNone(result.uvi_result)
        self.assertTrue(result.uvi_result.recorded)
        self.assertEqual(result.uvi_result.status, "RECORDED")
        self.assertEqual(
            Decimal(result.uvi_result.metadata["target_amount"]),
            Decimal("1"),
        )

        # Settlement
        self.assertIsNotNone(result.settlement_record)
        self.assertEqual(result.settlement_record.status, "SETTLED")
        self.assertEqual(result.settlement_record.unit, "SHIR")

        # Reconciliation
        self.assertIsNotNone(result.reconciliation_decision)
        self.assertEqual(
            result.reconciliation_decision.status,
            "MATCHED",
        )
        self.assertEqual(
            result.reconciliation_decision.difference,
            "0",
        )

    def test_risk_and_idempotency_gate_before_market_execution(self):
        from financial_core.exchange.contracts import ExchangeRequest

        request = ExchangeRequest(
            operation_id="EX017-GATE-001",
            user_id="USER-EX017",
            source_unit="POINT",
            target_unit="SHIR",
            source_amount="1000",
            quoted_target_amount="1",
            conversion_rate="0.001",
            fee_amount="0",
        )

        pipeline, ledger = self._pipeline_with_uvi("USER-EX017")

        result = pipeline.execute(
            request=request,
            buy_order=Order(
                order_id="BUY-EX017-GATE-001",
                market_id="2FUNC-SHIR",
                account_id="BUYER-EX017",
                side="BUY",
                order_type=OrderType.LIMIT,
                quantity=Decimal("5"),
                price=Decimal("20"),
                status="OPEN",
                time_in_force=TimeInForce.GTC,
            ),
            sell_order=Order(
                order_id="SELL-EX017-GATE-001",
                market_id="2FUNC-SHIR",
                account_id="SELLER-EX017",
                side="SELL",
                order_type=OrderType.LIMIT,
                quantity=Decimal("5"),
                price=Decimal("20"),
                status="OPEN",
                time_in_force=TimeInForce.GTC,
            ),
        )

        self.assertEqual(result.trade.quantity, Decimal("5"))
        self.assertEqual(result.fee.fee_amount, Decimal("0.2500"))
        self.assertEqual(result.operation_id, "EX017-GATE-001")
        self.assertEqual(result.risk_decision.approved, True)
        self.assertEqual(result.idempotency_decision.accepted, True)

if __name__ == "__main__":
    unittest.main()

