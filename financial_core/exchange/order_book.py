"""Exchange order book domain."""

from dataclasses import dataclass, field
from typing import Any

from financial_core.exchange.order import Order
from financial_core.exchange.order_types import OrderType


RESTING_ORDER_TYPES = {
    OrderType.LIMIT,
    OrderType.STOP_LIMIT,
}


@dataclass
class OrderBook:
    """Maintain resting BUY and SELL orders for one market."""

    market_id: str
    bids: list[Order] = field(default_factory=list)
    asks: list[Order] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_order(self, order: Order) -> None:
        """Add a valid resting order to the correct side of the book."""

        if order.market_id != self.market_id:
            raise ValueError("order market does not match order book market")

        order_type = OrderType(order.order_type)

        if order_type not in RESTING_ORDER_TYPES:
            raise ValueError("order type cannot rest on the order book")

        if order.side == "BUY":
            self.bids.append(order)
        else:
            self.asks.append(order)

    def sorted_bids(self) -> list[Order]:
        """Return BUY orders using price-time priority."""

        return sorted(
            self.bids,
            key=lambda order: -float(order.price),
        )

    def sorted_asks(self) -> list[Order]:
        """Return SELL orders using price-time priority."""

        return sorted(
            self.asks,
            key=lambda order: float(order.price),
        )

    def best_bid(self) -> Order | None:
        """Return the highest-priority BUY order."""

        bids = self.sorted_bids()
        return bids[0] if bids else None

    def best_ask(self) -> Order | None:
        """Return the highest-priority SELL order."""

        asks = self.sorted_asks()
        return asks[0] if asks else None
