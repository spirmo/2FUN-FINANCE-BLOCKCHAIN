import unittest
from decimal import Decimal

from financial_core.exchange.fee import FeeCalculator
from financial_core.exchange.trade import Trade


class TestFeeCalculator(unittest.TestCase):

    def make_trade(self):
        return Trade(
            trade_id="TRADE-FEE-001",
            market_id="2FUNC-USD",
            buy_order_id="BUY-001",
            sell_order_id="SELL-001",
            quantity=Decimal("3"),
            price=Decimal("20"),
        )

    def test_calculates_fee_from_trade_notional(self):
        trade = self.make_trade()

        result = FeeCalculator("0.001").calculate(trade)

        self.assertEqual(result.trade_id, "TRADE-FEE-001")
        self.assertEqual(result.fee_rate, Decimal("0.001"))
        self.assertEqual(result.fee_amount, Decimal("0.060"))

    def test_zero_fee_rate(self):
        trade = self.make_trade()

        result = FeeCalculator("0").calculate(trade)

        self.assertEqual(result.fee_amount, Decimal("0"))

    def test_rejects_negative_fee_rate(self):
        with self.assertRaises(ValueError):
            FeeCalculator("-0.001")


if __name__ == "__main__":
    unittest.main()


class TestFeeTradeIntegration(unittest.TestCase):

    def test_trade_to_fee_end_to_end(self):
        trade = Trade(
            trade_id="TRADE-E2E-FEE",
            market_id="2FUNC-USD",
            buy_order_id="BUY-E2E",
            sell_order_id="SELL-E2E",
            quantity=Decimal("5"),
            price=Decimal("20"),
        )

        result = FeeCalculator("0.0025").calculate(trade)

        self.assertEqual(trade.notional, Decimal("100"))
        self.assertEqual(result.trade_id, "TRADE-E2E-FEE")
        self.assertEqual(result.fee_rate, Decimal("0.0025"))
        self.assertEqual(result.fee_amount, Decimal("0.250"))


if __name__ == "__main__":
    unittest.main()
