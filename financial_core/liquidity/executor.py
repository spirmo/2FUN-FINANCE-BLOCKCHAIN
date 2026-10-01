"""Liquidity pool execution and registry."""

from financial_core.liquidity.contracts import (
    LiquidityDecision,
    LiquidityPool,
)
from financial_core.liquidity.validator import LiquidityValidator


class LiquidityExecutor:
    """
    Manage validated liquidity pools.

    Liquidity does not own value balances.
    It stores liquidity availability metadata only.
    """

    def __init__(self):
        self._validator = LiquidityValidator()
        self._pools: dict[str, LiquidityPool] = {}

    def register(
        self,
        pool: LiquidityPool,
    ) -> LiquidityDecision:
        decision = self._validator.validate(pool)

        if not decision.approved:
            raise ValueError(decision.reason)

        if pool.pool_id in self._pools:
            raise ValueError("liquidity pool already exists")

        self._pools[pool.pool_id] = pool

        return decision

    def get(
        self,
        pool_id: str,
    ) -> LiquidityPool | None:
        return self._pools.get(pool_id)

    def all_pools(self) -> tuple[LiquidityPool, ...]:
        return tuple(self._pools.values())
