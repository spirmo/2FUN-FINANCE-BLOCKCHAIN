"""Reconciliation domain contracts."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ReconciliationRequest:
    """Request to compare expected and recorded financial values."""

    operation_id: str
    expected_amount: str
    recorded_amount: str
    unit: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ReconciliationDecision:
    """Result of a reconciliation comparison."""

    operation_id: str
    status: str
    difference: str
    reason: str | None = None
