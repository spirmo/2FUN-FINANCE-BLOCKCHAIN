import unittest

from financial_core.exchange.order import Order
from financial_core.exchange.order_book import OrderBook


class TestOrderBook(unittest.TestCase):

    def make_order(
        self,
        order_id,
        side="BUY",
        order_type="LIMIT",
        market_id="2FUNC-USD",
    ):
        return Order(
            order_id=order_id,
            market_id=market_id,
            account_id="ACC-001",
            side=side,
            order_type=order_type,
            quantity="1",
            price="20",
        )

    def test_add_buy_order(self):
        book = OrderBook("2FUNC-USD")
        order = self.make_order("BUY-001", side="BUY")

        book.add_order(order)

        self.assertEqual(book.bids, [order])
        self.assertEqual(book.asks, [])

    def test_add_sell_order(self):
        book = OrderBook("2FUNC-USD")
        order = self.make_order("SELL-001", side="SELL")

        book.add_order(order)

        self.assertEqual(book.asks, [order])
        self.assertEqual(book.bids, [])

    def test_rejects_order_from_different_market(self):
        book = OrderBook("2FUNC-USD")
        order = self.make_order(
            "OTHER-001",
            market_id="2FUNC-CAD",
        )

        with self.assertRaises(ValueError):
            book.add_order(order)

    def test_rejects_market_order_from_book(self):
        book = OrderBook("2FUNC-USD")

        order = Order(
            order_id="MARKET-001",
            market_id="2FUNC-USD",
            account_id="ACC-001",
            side="BUY",
            order_type="MARKET",
            quantity="1",
        )

        with self.assertRaises(ValueError):
            book.add_order(order)

    def test_rejects_stop_order_from_book(self):
        book = OrderBook("2FUNC-USD")

        order = Order(
            order_id="STOP-001",
            market_id="2FUNC-USD",
            account_id="ACC-001",
            side="BUY",
            order_type="STOP",
            quantity="1",
            stop_price="20",
        )

        with self.assertRaises(ValueError):
            book.add_order(order)


if __name__ == "__main__":
    unittest.main()
