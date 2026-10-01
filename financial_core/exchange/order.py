"""Exchange order domain model."""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


ORDER_SIDES = {"BUY", "SELL"}
ORDER_STATUSES = {"OPEN", "PARTIALLY_FILLED", "FILLED", "CANCELLED", "REJECTED"}


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

        if not self.order_type:
            raise ValueError("order_type is required")

        try:
            quantity = Decimal(self.quantity)
        except (InvalidOperation, ValueError):
            raise ValueError("quantity must be a valid decimal")

        if quantity <= 0:
            raise ValueError("quantity must be greater than zero")

        if self.price is not None:
            try:
                price = Decimal(self.price)
            except (InvalidOperation, ValueError):
                raise ValueError("price must be a valid decimal")

            if price <= 0:
                raise ValueError("price must be greater than zero")

        if self.status not in ORDER_STATUSES:
            raise ValueError("invalid order status")
