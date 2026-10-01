"""Financial transfer contract."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class TransferRequest:
    """Immutable account-to-account transfer request."""

    operation_id: str
    source_account_id: str
    destination_account_id: str
    amount: str
    unit: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class TransferValidationResult:
    """Result of transfer request validation."""

    operation_id: str
    valid: bool
    reason: str | None = None
