"""Price-adjusted reward calculation."""

from decimal import Decimal

from financial_core.contracts.reward import (
    RewardCalculationRequest,
    RewardCalculationResult,
)


class PriceAdjustedRewardCalculator:
    """Calculate rewards relative to the current 2FUNC valuation."""

    def calculate(
        self,
        request: RewardCalculationRequest,
    ) -> RewardCalculationResult:
        if request.base_reward < 0:
            raise ValueError("base_reward cannot be negative")

        if request.reference_price <= 0:
            raise ValueError("reference_price must be positive")

        if request.current_price <= 0:
            raise ValueError("current_price must be positive")

        adjustment_factor = (
            request.reference_price / request.current_price
        )

        adjusted_reward = (
            request.base_reward * adjustment_factor
        )

        return RewardCalculationResult(
            operation_id=request.operation_id,
            base_reward=request.base_reward,
            reference_price=request.reference_price,
            current_price=request.current_price,
            adjusted_reward=adjusted_reward,
            reward_unit=request.reward_unit,
            valuation_asset=request.valuation_asset,
            quote_asset=request.quote_asset,
            adjustment_factor=adjustment_factor,
            metadata=dict(request.metadata or {}),
        )
