"""Reward execution contract.

Defines the complete result of a value-aware reward execution.
Financial state remains owned by UVI.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping


@dataclass(frozen=True)
class RewardExecutionRequest:
    """Request for executing a value-adjusted reward."""

    operation_id: str
    user_id: str
    base_reward: Decimal
    reference_price: Decimal
    current_price: Decimal
    reward_unit: str = "POINT"
    valuation_asset: str = "2FUNC"
    quote_asset: str = "STABLECOIN"
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class RewardExecutionResult:
    """Immutable result of a completed reward execution."""

    operation_id: str
    user_id: str
    status: str
    base_reward: Decimal
    adjusted_reward: Decimal
    reference_price: Decimal
    current_price: Decimal
    adjustment_factor: Decimal
    reward_unit: str
    valuation_asset: str
    quote_asset: str
    uvi_transaction_id: str
    integrity_hash: str
    idempotent: bool
    metadata: Mapping[str, Any]
