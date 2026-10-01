"""Exchange matching engine domain."""

from dataclasses import dataclass
from decimal import Decimal

from financial_core.exchange.order import Order
from financial_core.exchange.order_book import OrderBook


@dataclass(frozen=True)
class MatchResult:
    """Result of matching one BUY order against one SELL order."""

    buy_order: Order
    sell_order: Order
    quantity: Decimal
    price: Decimal


class MatchingEngine:
    """Match the best BUY and SELL orders from an order book."""

    def match(self, order_book: OrderBook) -> MatchResult | None:
        """Return one executable match, or None when no match exists."""

        buy = order_book.best_bid()
        sell = order_book.best_ask()

        if buy is None or sell is None:
            return None

        buy_price = Decimal(str(buy.price))
        sell_price = Decimal(str(sell.price))

        if buy_price < sell_price:
            return None

        quantity = min(
            Decimal(str(buy.quantity)),
            Decimal(str(sell.quantity)),
        )

        price = sell_price

        return MatchResult(
            buy_order=buy,
            sell_order=sell,
            quantity=quantity,
            price=price,
        )
