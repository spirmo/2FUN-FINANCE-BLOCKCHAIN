"""Internal transfer domain contracts."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class InternalTransferRequest:
    """Request to transfer value between two users inside the system."""

    operation_id: str
    source_user_id: str
    target_user_id: str
    amount: str
    unit: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class InternalTransferDecision:
    """Validation decision for an internal transfer."""

    operation_id: str
    approved: bool
    reason: str | None = None


@dataclass(frozen=True)
class InternalTransferRecord:
    """Immutable record of an internal transfer."""

    operation_id: str
    source_user_id: str
    target_user_id: str
    amount: str
    unit: str
    status: str
    source_transaction_id: str | None = None
    target_transaction_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
