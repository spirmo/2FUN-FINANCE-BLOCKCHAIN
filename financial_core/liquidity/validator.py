"""Liquidity validation."""

from decimal import Decimal, InvalidOperation

from financial_core.liquidity.contracts import (
    LiquidityDecision,
    LiquidityPool,
)


class LiquidityValidator:
    """Validate liquidity pool definitions without mutating state."""

    def validate(
        self,
        pool: LiquidityPool,
    ) -> LiquidityDecision:
        if not pool.pool_id:
            return LiquidityDecision(
                pool.pool_id,
                False,
                "pool_id is required",
            )

        if not pool.market_id:
            return LiquidityDecision(
                pool.pool_id,
                False,
                "market_id is required",
            )

        if not pool.base_unit or not pool.quote_unit:
            return LiquidityDecision(
                pool.pool_id,
                False,
                "base_unit and quote_unit are required",
            )

        if pool.base_unit == pool.quote_unit:
            return LiquidityDecision(
                pool.pool_id,
                False,
                "base and quote units must differ",
            )

        try:
            base_reserve = Decimal(pool.base_reserve)
            quote_reserve = Decimal(pool.quote_reserve)
        except (InvalidOperation, ValueError):
            return LiquidityDecision(
                pool.pool_id,
                False,
                "reserves must be valid decimals",
            )

        if base_reserve <= 0 or quote_reserve <= 0:
            return LiquidityDecision(
                pool.pool_id,
                False,
                "reserves must be greater than zero",
            )

        if pool.status != "ACTIVE":
            return LiquidityDecision(
                pool.pool_id,
                False,
                "liquidity pool must be ACTIVE",
            )

        return LiquidityDecision(
            pool.pool_id,
            True,
        )
