"""Financial payment contract."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class PaymentRequest:
    """Immutable payment request backed by the existing transfer path."""

    operation_id: str
    payer_account_id: str
    payee_account_id: str
    amount: str
    unit: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PaymentValidationResult:
    """Result of payment request validation."""

    operation_id: str
    valid: bool
    reason: str | None = None
