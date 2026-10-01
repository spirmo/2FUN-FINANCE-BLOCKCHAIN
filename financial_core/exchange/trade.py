"""Exchange trade domain."""

from dataclasses import dataclass
from decimal import Decimal

from financial_core.exchange.matching import MatchResult
from financial_core.exchange.order import Order


@dataclass(frozen=True)
class Trade:
    """A completed exchange execution between a BUY and SELL order."""

    trade_id: str
    market_id: str
    buy_order_id: str
    sell_order_id: str
    quantity: Decimal
    price: Decimal

    @property
    def notional(self) -> Decimal:
        """Return the gross trade value."""

        return self.quantity * self.price

    @classmethod
    def from_match_result(
        cls,
        trade_id: str,
        match: MatchResult,
    ) -> "Trade":
        """Create a Trade directly from a matching result."""

        return cls.from_execution(
            trade_id=trade_id,
            buy_order=match.buy_order,
            sell_order=match.sell_order,
            quantity=match.quantity,
            price=match.price,
        )

    @classmethod
    def from_execution(
        cls,
        trade_id: str,
        buy_order: Order,
        sell_order: Order,
        quantity: Decimal,
        price: Decimal,
    ) -> "Trade":
        """Create a Trade from a matching execution."""

        if buy_order.side != "BUY":
            raise ValueError("buy_order must have BUY side")

        if sell_order.side != "SELL":
            raise ValueError("sell_order must have SELL side")

        if buy_order.market_id != sell_order.market_id:
            raise ValueError("orders must belong to the same market")

        if quantity <= 0:
            raise ValueError("trade quantity must be positive")

        if price <= 0:
            raise ValueError("trade price must be positive")

        return cls(
            trade_id=trade_id,
            market_id=buy_order.market_id,
            buy_order_id=buy_order.order_id,
            sell_order_id=sell_order.order_id,
            quantity=quantity,
            price=price,
        )
