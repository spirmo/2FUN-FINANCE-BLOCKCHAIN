import unittest

from financial_core.exchange.order import Order
from financial_core.exchange.order_types import (
    OrderType,
    TimeInForce,
    requires_price,
    requires_stop_price,
)


class TestOrderTypes(unittest.TestCase):

    def test_order_type_definitions(self):
        self.assertEqual(OrderType.MARKET.value, "MARKET")
        self.assertEqual(OrderType.LIMIT.value, "LIMIT")
        self.assertEqual(OrderType.STOP.value, "STOP")
        self.assertEqual(OrderType.STOP_LIMIT.value, "STOP_LIMIT")

    def test_time_in_force_definitions(self):
        self.assertEqual(TimeInForce.GTC.value, "GTC")
        self.assertEqual(TimeInForce.IOC.value, "IOC")
        self.assertEqual(TimeInForce.FOK.value, "FOK")

    def test_price_requirements(self):
        self.assertFalse(requires_price(OrderType.MARKET))
        self.assertTrue(requires_price(OrderType.LIMIT))
        self.assertFalse(requires_price(OrderType.STOP))
        self.assertTrue(requires_price(OrderType.STOP_LIMIT))

    def test_stop_price_requirements(self):
        self.assertFalse(requires_stop_price(OrderType.MARKET))
        self.assertFalse(requires_stop_price(OrderType.LIMIT))
        self.assertTrue(requires_stop_price(OrderType.STOP))
        self.assertTrue(requires_stop_price(OrderType.STOP_LIMIT))

    def test_stop_order_requires_stop_price(self):
        with self.assertRaises(ValueError):
            Order(
                order_id="STOP-001",
                market_id="2FUNC-USD",
                account_id="ACC-001",
                side="BUY",
                order_type="STOP",
                quantity="1",
            )

    def test_stop_order_accepts_stop_price(self):
        order = Order(
            order_id="STOP-002",
            market_id="2FUNC-USD",
            account_id="ACC-001",
            side="BUY",
            order_type="STOP",
            quantity="1",
            stop_price="20",
        )

        self.assertEqual(order.stop_price, "20")

    def test_stop_limit_requires_both_prices(self):
        with self.assertRaises(ValueError):
            Order(
                order_id="STOP-LIMIT-001",
                market_id="2FUNC-USD",
                account_id="ACC-001",
                side="BUY",
                order_type="STOP_LIMIT",
                quantity="1",
                price="19",
            )

    def test_stop_limit_accepts_both_prices(self):
        order = Order(
            order_id="STOP-LIMIT-002",
            market_id="2FUNC-USD",
            account_id="ACC-001",
            side="SELL",
            order_type="STOP_LIMIT",
            quantity="1",
            price="19",
            stop_price="20",
            time_in_force="IOC",
        )

        self.assertEqual(order.price, "19")
        self.assertEqual(order.stop_price, "20")
        self.assertEqual(order.time_in_force, "IOC")

    def test_market_order_rejects_price(self):
        with self.assertRaises(ValueError):
            Order(
                order_id="MARKET-001",
                market_id="2FUNC-USD",
                account_id="ACC-001",
                side="BUY",
                order_type="MARKET",
                quantity="1",
                price="20",
            )

    def test_market_fok_is_rejected(self):
        with self.assertRaises(ValueError):
            Order(
                order_id="MARKET-002",
                market_id="2FUNC-USD",
                account_id="ACC-001",
                side="BUY",
                order_type="MARKET",
                quantity="1",
                time_in_force="FOK",
            )


if __name__ == "__main__":
    unittest.main()
