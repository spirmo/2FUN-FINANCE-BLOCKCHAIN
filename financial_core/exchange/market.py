"""Exchange market domain model."""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping


@dataclass(frozen=True)
class Market:
    """
    Trading market definition.

    A Market defines the relationship between a base unit and a quote unit.
    It does not own orders, order books, matching, settlement, or ledger state.
    """

    market_id: str
    base_unit: str
    quote_unit: str
    status: str = "ACTIVE"
    price_precision: int = 8
    quantity_precision: int = 8
    min_quantity: str = "0"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.market_id:
            raise ValueError("market_id is required")

        if not self.base_unit:
            raise ValueError("base_unit is required")

        if not self.quote_unit:
            raise ValueError("quote_unit is required")

        if self.base_unit == self.quote_unit:
            raise ValueError("base_unit and quote_unit must differ")

        if self.status not in {"ACTIVE", "INACTIVE", "SUSPENDED"}:
            raise ValueError("invalid market status")

        if self.price_precision < 0:
            raise ValueError("price_precision cannot be negative")

        if self.quantity_precision < 0:
            raise ValueError("quantity_precision cannot be negative")

        try:
            minimum = Decimal(self.min_quantity)
        except (InvalidOperation, ValueError):
            raise ValueError("min_quantity must be a valid decimal")

        if minimum < 0:
            raise ValueError("min_quantity cannot be negative")

    @property
    def symbol(self) -> str:
        """Return the canonical market symbol."""
        return f"{self.base_unit}/{self.quote_unit}"

    @property
    def is_active(self) -> bool:
        """Return whether the market accepts trading activity."""
        return self.status == "ACTIVE"
