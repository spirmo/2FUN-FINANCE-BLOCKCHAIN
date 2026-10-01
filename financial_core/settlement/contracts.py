"""Settlement domain contracts."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class SettlementRequest:
    """Request to finalize an approved financial operation."""

    operation_id: str
    settlement_type: str
    amount: str
    unit: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SettlementDecision:
    """Decision describing how an operation will be settled."""

    operation_id: str
    settlement_type: str
    approved: bool
    reason: str | None = None


@dataclass(frozen=True)
class SettlementRecord:
    """Immutable record of a completed or attempted settlement."""

    operation_id: str
    settlement_type: str
    amount: str
    unit: str
    status: str
    transaction_reference: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
