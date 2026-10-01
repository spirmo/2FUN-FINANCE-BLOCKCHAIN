import unittest
from decimal import Decimal

from financial_core.exchange.matching import MatchingEngine
from financial_core.exchange.order import Order
from financial_core.exchange.order_book import OrderBook


class TestMatchingEngine(unittest.TestCase):

    def make_order(
        self,
        order_id,
        side,
        quantity,
        price,
    ):
        return Order(
            order_id=order_id,
            market_id="2FUNC-USD",
            account_id="ACC-001",
            side=side,
            order_type="LIMIT",
            quantity=str(quantity),
            price=str(price),
        )

    def test_empty_book_returns_no_match(self):
        book = OrderBook("2FUNC-USD")
        engine = MatchingEngine()

        result = engine.match(book)

        self.assertIsNone(result)

    def test_non_crossing_orders_return_no_match(self):
        book = OrderBook("2FUNC-USD")

        buy = self.make_order("BUY-001", "BUY", "5", "19")
        sell = self.make_order("SELL-001", "SELL", "5", "20")

        book.add_order(buy)
        book.add_order(sell)

        result = MatchingEngine().match(book)

        self.assertIsNone(result)

    def test_crossing_orders_create_match(self):
        book = OrderBook("2FUNC-USD")

        buy = self.make_order("BUY-001", "BUY", "5", "21")
        sell = self.make_order("SELL-001", "SELL", "5", "20")

        book.add_order(buy)
        book.add_order(sell)

        result = MatchingEngine().match(book)

        self.assertIsNotNone(result)
        self.assertEqual(result.buy_order.order_id, "BUY-001")
        self.assertEqual(result.sell_order.order_id, "SELL-001")
        self.assertEqual(result.quantity, Decimal("5"))
        self.assertEqual(result.price, Decimal("20"))

    def test_match_quantity_is_minimum_available_quantity(self):
        book = OrderBook("2FUNC-USD")

        buy = self.make_order("BUY-001", "BUY", "3", "21")
        sell = self.make_order("SELL-001", "SELL", "5", "20")

        book.add_order(buy)
        book.add_order(sell)

        result = MatchingEngine().match(book)

        self.assertIsNotNone(result)
        self.assertEqual(result.quantity, Decimal("3"))


if __name__ == "__main__":
    unittest.main()

class TestMatchingExecutionPrice(unittest.TestCase):

    def make_order(self, order_id, side, quantity, price):
        return Order(
            order_id=order_id,
            market_id="2FUNC-USD",
            account_id="ACC-001",
            side=side,
            order_type="LIMIT",
            quantity=str(quantity),
            price=str(price),
        )

    def test_execution_price_uses_resting_sell_price(self):
        book = OrderBook("2FUNC-USD")

        buy = self.make_order("BUY-001", "BUY", "5", "21")
        sell = self.make_order("SELL-001", "SELL", "5", "20")

        book.add_order(buy)
        book.add_order(sell)

        result = MatchingEngine().match(book)

        self.assertIsNotNone(result)
        self.assertEqual(result.price, Decimal("20"))


if __name__ == "__main__":
    unittest.main()

class TestMatchingBestOrders(unittest.TestCase):

    def make_order(self, order_id, side, quantity, price):
        return Order(
            order_id=order_id,
            market_id="2FUNC-USD",
            account_id="ACC-001",
            side=side,
            order_type="LIMIT",
            quantity=str(quantity),
            price=str(price),
        )

    def test_matching_uses_best_bid_and_best_ask(self):
        book = OrderBook("2FUNC-USD")

        buy_low = self.make_order("BUY-LOW", "BUY", "5", "19")
        buy_best = self.make_order("BUY-BEST", "BUY", "3", "21")

        sell_high = self.make_order("SELL-HIGH", "SELL", "5", "22")
        sell_best = self.make_order("SELL-BEST", "SELL", "2", "20")

        book.add_order(buy_low)
        book.add_order(buy_best)
        book.add_order(sell_high)
        book.add_order(sell_best)

        result = MatchingEngine().match(book)

        self.assertIsNotNone(result)
        self.assertEqual(result.buy_order.order_id, "BUY-BEST")
        self.assertEqual(result.sell_order.order_id, "SELL-BEST")
        self.assertEqual(result.quantity, Decimal("2"))
        self.assertEqual(result.price, Decimal("20"))


if __name__ == "__main__":
    unittest.main()
