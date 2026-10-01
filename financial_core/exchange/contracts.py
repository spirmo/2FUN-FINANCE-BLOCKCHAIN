"""Exchange domain contracts."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class ExchangeRequest:
    """Request to execute an exchange between two value units."""

    operation_id: str
    source_unit: str
    target_unit: str
    source_amount: str
    quoted_target_amount: str
    fee_amount: str = "0"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExchangeDecision:
    """Validation decision for an exchange request."""

    operation_id: str
    approved: bool
    reason: str | None = None


@dataclass(frozen=True)
class ExchangeResult:
    """Result of an exchange execution."""

    operation_id: str
    source_unit: str
    target_unit: str
    source_amount: str
    target_amount: str
    fee_amount: str
    status: str
    settlement_request: Any | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
