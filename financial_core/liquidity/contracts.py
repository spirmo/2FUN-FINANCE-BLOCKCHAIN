"""Liquidity domain contracts."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class LiquidityPool:
    """Description of liquidity available for an exchange market."""

    pool_id: str
    market_id: str
    base_unit: str
    quote_unit: str
    base_reserve: str
    quote_reserve: str
    status: str = "ACTIVE"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class LiquidityDecision:
    """Validation decision for a liquidity pool."""

    pool_id: str
    approved: bool
    reason: str | None = None
