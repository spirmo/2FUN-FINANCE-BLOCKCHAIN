"""Exchange order domain model."""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

from financial_core.exchange.order_types import (
    OrderType,
    TimeInForce,
    requires_price,
    requires_stop_price,
)


ORDER_SIDES = {"BUY", "SELL"}
ORDER_STATUSES = {
    "OPEN",
    "PARTIALLY_FILLED",
    "FILLED",
    "CANCELLED",
    "REJECTED",
}


@dataclass(frozen=True)
class Order:
    """Represent a validated exchange order."""

    order_id: str
    market_id: str
    account_id: str
    side: str
    order_type: str
    quantity: str
    price: str | None = None
    stop_price: str | None = None
    time_in_force: str = "GTC"
    status: str = "OPEN"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.order_id:
            raise ValueError("order_id is required")

        if not self.market_id:
            raise ValueError("market_id is required")

        if not self.account_id:
            raise ValueError("account_id is required")

        if self.side not in ORDER_SIDES:
            raise ValueError("side must be BUY or SELL")

        try:
            order_type = OrderType(self.order_type)
        except ValueError:
            raise ValueError("invalid order type")

        try:
            time_in_force = TimeInForce(self.time_in_force)
        except ValueError:
            raise ValueError("invalid time in force")

        try:
            quantity = Decimal(self.quantity)
        except (InvalidOperation, ValueError):
            raise ValueError("quantity must be a valid decimal")

        if quantity <= 0:
            raise ValueError("quantity must be greater than zero")

        if requires_price(order_type) and self.price is None:
            raise ValueError("this order type requires a price")

        if order_type is OrderType.MARKET and self.price is not None:
            raise ValueError("market orders must not specify a price")

        if requires_stop_price(order_type) and self.stop_price is None:
            raise ValueError("this order type requires a stop price")

        if order_type in {OrderType.MARKET, OrderType.LIMIT} and self.stop_price is not None:
            raise ValueError("this order type must not specify a stop price")

        if time_in_force is TimeInForce.FOK and order_type is OrderType.MARKET:
            raise ValueError("FOK market orders are not supported")

        if self.price is not None:
            try:
                price = Decimal(self.price)
            except (InvalidOperation, ValueError):
                raise ValueError("price must be a valid decimal")

            if price <= 0:
                raise ValueError("price must be greater than zero")

        if self.stop_price is not None:
            try:
                stop_price = Decimal(self.stop_price)
            except (InvalidOperation, ValueError):
                raise ValueError("stop_price must be a valid decimal")

            if stop_price <= 0:
                raise ValueError("stop_price must be greater than zero")

        if self.status not in ORDER_STATUSES:
            raise ValueError("invalid order status")
