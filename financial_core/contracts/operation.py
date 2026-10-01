"""Financial operation contract.

This module defines the neutral contract shared by Financial Core
operations. It does not own value calculation, ledger state, or
blockchain state.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping


@dataclass(frozen=True)
class FinancialOperationRequest:
    """Immutable request entering the Financial Core."""

    operation_id: str
    operation_type: str
    user_id: str
    amount: str
    unit: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
    requested_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


@dataclass(frozen=True)
class FinancialOperationResult:
    """Immutable result returned by a Financial Core operation."""

    operation_id: str
    status: str
    settlement_required: bool
    metadata: Mapping[str, Any] = field(default_factory=dict)
