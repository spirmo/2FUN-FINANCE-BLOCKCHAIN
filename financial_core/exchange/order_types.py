"""Exchange order type definitions."""

from enum import Enum


class OrderType(str, Enum):
    """Supported exchange order types."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class TimeInForce(str, Enum):
    """Supported order lifetime and execution policies."""

    GTC = "GTC"
    IOC = "IOC"
    FOK = "FOK"


def requires_price(order_type: OrderType) -> bool:
    """Return whether an order type requires a limit price."""
    return order_type in {
        OrderType.LIMIT,
        OrderType.STOP_LIMIT,
    }


def requires_stop_price(order_type: OrderType) -> bool:
    """Return whether an order type requires a trigger price."""
    return order_type in {
        OrderType.STOP,
        OrderType.STOP_LIMIT,
    }
