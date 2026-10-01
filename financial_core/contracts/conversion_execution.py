"""Execution contracts for 2FUNC value conversion."""

from dataclasses import dataclass
from decimal import Decimal
from typing import Any, Mapping


@dataclass(frozen=True)
class ConversionExecutionRequest:
    operation_id: str
    user_id: str
    source_unit: str
    target_unit: str
    amount: Decimal
    metadata: Mapping[str, Any] | None = None


@dataclass(frozen=True)
class ConversionExecutionResult:
    operation_id: str
    user_id: str
    status: str
    source_unit: str
    target_unit: str
    source_amount: Decimal
    target_amount: Decimal
    remainder_amount: Decimal
    integrity_hash: str
    source_transaction_id: str
    target_transaction_id: str
    idempotent: bool
    metadata: Mapping[str, Any]
