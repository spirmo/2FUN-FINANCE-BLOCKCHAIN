"""Dynamic reward calculation contracts."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class RewardCalculationRequest:
    """Inputs required for value-adjusted reward calculation."""

    operation_id: str
    base_reward: Decimal
    reference_price: Decimal
    current_price: Decimal
    reward_unit: str = "POINT"
    valuation_asset: str = "2FUNC"
    quote_asset: str = "STABLECOIN"
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class RewardCalculationResult:
    """Calculated reward without mutating financial state."""

    operation_id: str
    base_reward: Decimal
    reference_price: Decimal
    current_price: Decimal
    adjusted_reward: Decimal
    reward_unit: str
    valuation_asset: str
    quote_asset: str
    adjustment_factor: Decimal
    metadata: Mapping[str, Any]


class RewardCalculator(Protocol):
    """Contract for value-aware reward calculation."""

    def calculate(
        self,
        request: RewardCalculationRequest,
    ) -> RewardCalculationResult:
        """Calculate an adjusted reward without ledger mutation."""
        ...
