"""EX-002 Market tests using Python standard library."""

import unittest

from financial_core.exchange.market import Market


class TestMarket(unittest.TestCase):

    def test_market_creation(self):
        market = Market(
            market_id="2FUNC-USD",
            base_unit="2FUNC",
            quote_unit="USD",
            price_precision=8,
            quantity_precision=8,
            min_quantity="0.00000001",
        )

        self.assertEqual(market.market_id, "2FUNC-USD")
        self.assertEqual(market.base_unit, "2FUNC")
        self.assertEqual(market.quote_unit, "USD")
        self.assertEqual(market.symbol, "2FUNC/USD")
        self.assertEqual(market.status, "ACTIVE")
        self.assertTrue(market.is_active)

    def test_market_rejects_same_base_and_quote(self):
        with self.assertRaisesRegex(ValueError, "must differ"):
            Market(
                market_id="INVALID",
                base_unit="2FUNC",
                quote_unit="2FUNC",
            )

    def test_market_rejects_invalid_status(self):
        with self.assertRaisesRegex(ValueError, "invalid market status"):
            Market(
                market_id="2FUNC-USD",
                base_unit="2FUNC",
                quote_unit="USD",
                status="UNKNOWN",
            )

    def test_market_rejects_negative_min_quantity(self):
        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            Market(
                market_id="2FUNC-USD",
                base_unit="2FUNC",
                quote_unit="USD",
                min_quantity="-1",
            )

    def test_market_can_be_suspended(self):
        market = Market(
            market_id="2FUNC-USD",
            base_unit="2FUNC",
            quote_unit="USD",
            status="SUSPENDED",
        )

        self.assertFalse(market.is_active)


if __name__ == "__main__":
    unittest.main()
