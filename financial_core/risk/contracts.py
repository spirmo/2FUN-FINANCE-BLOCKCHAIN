"""Risk and security domain contracts."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class RiskRequest:
    """Request evaluated by the financial risk gate."""

    operation_id: str
    settlement_type: str
    amount: str
    unit: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskDecision:
    """Immutable risk decision."""

    operation_id: str
    approved: bool
    reason: str | None = None
