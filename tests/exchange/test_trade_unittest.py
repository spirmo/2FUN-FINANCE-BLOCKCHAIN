import unittest
from decimal import Decimal

from financial_core.exchange.order import Order
from financial_core.exchange.matching import MatchingEngine
from financial_core.exchange.order_book import OrderBook
from financial_core.exchange.trade import Trade


class TestTrade(unittest.TestCase):

    def make_order(self, order_id, side, market_id="2FUNC-USD"):
        return Order(
            order_id=order_id,
            market_id=market_id,
            account_id="ACC-001",
            side=side,
            order_type="LIMIT",
            quantity="5",
            price="20",
        )

    def test_create_trade_from_execution(self):
        buy = self.make_order("BUY-001", "BUY")
        sell = self.make_order("SELL-001", "SELL")

        trade = Trade.from_execution(
            trade_id="TRADE-001",
            buy_order=buy,
            sell_order=sell,
            quantity=Decimal("3"),
            price=Decimal("20"),
        )

        self.assertEqual(trade.trade_id, "TRADE-001")
        self.assertEqual(trade.market_id, "2FUNC-USD")
        self.assertEqual(trade.buy_order_id, "BUY-001")
        self.assertEqual(trade.sell_order_id, "SELL-001")
        self.assertEqual(trade.quantity, Decimal("3"))
        self.assertEqual(trade.price, Decimal("20"))

    def test_notional_is_quantity_times_price(self):
        buy = self.make_order("BUY-001", "BUY")
        sell = self.make_order("SELL-001", "SELL")

        trade = Trade.from_execution(
            trade_id="TRADE-001",
            buy_order=buy,
            sell_order=sell,
            quantity=Decimal("3"),
            price=Decimal("20"),
        )

        self.assertEqual(trade.notional, Decimal("60"))

    def test_rejects_invalid_buy_side(self):
        buy = self.make_order("BUY-001", "SELL")
        sell = self.make_order("SELL-001", "SELL")

        with self.assertRaises(ValueError):
            Trade.from_execution(
                trade_id="TRADE-001",
                buy_order=buy,
                sell_order=sell,
                quantity=Decimal("1"),
                price=Decimal("20"),
            )

    def test_rejects_invalid_sell_side(self):
        buy = self.make_order("BUY-001", "BUY")
        sell = self.make_order("SELL-001", "BUY")

        with self.assertRaises(ValueError):
            Trade.from_execution(
                trade_id="TRADE-001",
                buy_order=buy,
                sell_order=sell,
                quantity=Decimal("1"),
                price=Decimal("20"),
            )

    def test_rejects_different_markets(self):
        buy = self.make_order("BUY-001", "BUY", "2FUNC-USD")
        sell = self.make_order("SELL-001", "SELL", "2FUNC-CAD")

        with self.assertRaises(ValueError):
            Trade.from_execution(
                trade_id="TRADE-001",
                buy_order=buy,
                sell_order=sell,
                quantity=Decimal("1"),
                price=Decimal("20"),
            )

    def test_rejects_non_positive_quantity(self):
        buy = self.make_order("BUY-001", "BUY")
        sell = self.make_order("SELL-001", "SELL")

        with self.assertRaises(ValueError):
            Trade.from_execution(
                trade_id="TRADE-001",
                buy_order=buy,
                sell_order=sell,
                quantity=Decimal("0"),
                price=Decimal("20"),
            )

    def test_rejects_non_positive_price(self):
        buy = self.make_order("BUY-001", "BUY")
        sell = self.make_order("SELL-001", "SELL")

        with self.assertRaises(ValueError):
            Trade.from_execution(
                trade_id="TRADE-001",
                buy_order=buy,
                sell_order=sell,
                quantity=Decimal("1"),
                price=Decimal("0"),
            )


if __name__ == "__main__":
    unittest.main()

class TestTradeFromMatchResult(unittest.TestCase):

    def test_match_result_converts_to_trade(self):
        book = OrderBook("2FUNC-USD")

        buy = Order(
            order_id="BUY-001",
            market_id="2FUNC-USD",
            account_id="ACC-BUY",
            side="BUY",
            order_type="LIMIT",
            quantity="5",
            price="21",
        )

        sell = Order(
            order_id="SELL-001",
            market_id="2FUNC-USD",
            account_id="ACC-SELL",
            side="SELL",
            order_type="LIMIT",
            quantity="3",
            price="20",
        )

        book.add_order(buy)
        book.add_order(sell)

        match = MatchingEngine().match(book)

        self.assertIsNotNone(match)

        trade = Trade.from_match_result(
            trade_id="TRADE-001",
            match=match,
        )

        self.assertEqual(trade.trade_id, "TRADE-001")
        self.assertEqual(trade.buy_order_id, "BUY-001")
        self.assertEqual(trade.sell_order_id, "SELL-001")
        self.assertEqual(trade.quantity, Decimal("3"))
        self.assertEqual(trade.price, Decimal("20"))
        self.assertEqual(trade.notional, Decimal("60"))


if __name__ == "__main__":
    unittest.main()
