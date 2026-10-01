"""Financial operation execution contract.

This contract describes the result of executing a financial operation.
It does not own ledger, account, settlement, or blockchain state.
"""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class FinancialExecutionResult:
    """Immutable result of an executed financial operation."""

    operation_id: str
    status: str
    value_recorded: bool
    settlement_required: bool
    settlement_type: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
