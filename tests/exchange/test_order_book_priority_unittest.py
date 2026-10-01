import unittest

from financial_core.exchange.order import Order
from financial_core.exchange.order_book import OrderBook


class TestOrderBookPriority(unittest.TestCase):

    def make_order(
        self,
        order_id,
        side,
        price,
    ):
        return Order(
            order_id=order_id,
            market_id="2FUNC-USD",
            account_id="ACC-001",
            side=side,
            order_type="LIMIT",
            quantity="1",
            price=str(price),
        )

    def test_best_bid_is_highest_price(self):
        book = OrderBook("2FUNC-USD")

        low = self.make_order("BUY-LOW", "BUY", "19")
        high = self.make_order("BUY-HIGH", "BUY", "21")

        book.add_order(low)
        book.add_order(high)

        self.assertEqual(book.best_bid().order_id, "BUY-HIGH")

    def test_best_ask_is_lowest_price(self):
        book = OrderBook("2FUNC-USD")

        high = self.make_order("SELL-HIGH", "SELL", "21")
        low = self.make_order("SELL-LOW", "SELL", "19")

        book.add_order(high)
        book.add_order(low)

        self.assertEqual(book.best_ask().order_id, "SELL-LOW")

    def test_equal_bid_price_preserves_fifo(self):
        book = OrderBook("2FUNC-USD")

        first = self.make_order("BUY-FIRST", "BUY", "20")
        second = self.make_order("BUY-SECOND", "BUY", "20")

        book.add_order(first)
        book.add_order(second)

        self.assertEqual(book.best_bid().order_id, "BUY-FIRST")

    def test_equal_ask_price_preserves_fifo(self):
        book = OrderBook("2FUNC-USD")

        first = self.make_order("SELL-FIRST", "SELL", "20")
        second = self.make_order("SELL-SECOND", "SELL", "20")

        book.add_order(first)
        book.add_order(second)

        self.assertEqual(book.best_ask().order_id, "SELL-FIRST")

    def test_empty_book_has_no_best_orders(self):
        book = OrderBook("2FUNC-USD")

        self.assertIsNone(book.best_bid())
        self.assertIsNone(book.best_ask())


if __name__ == "__main__":
    unittest.main()
