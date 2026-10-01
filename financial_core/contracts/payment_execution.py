"""Financial payment execution contract."""

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class PaymentExecutionResult:
    """Immutable result of a financial payment execution."""

    operation_id: str
    payment_id: str
    payer_account_id: str
    payee_account_id: str
    amount: str
    unit: str
    status: str
    transfer_operation_id: str
    payer_uvi_transaction_id: str | None = None
    payee_uvi_transaction_id: str | None = None
    financial_transaction_hash: str | None = None
    metadata: Mapping[str, Any] | None = None
