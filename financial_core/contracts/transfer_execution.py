"""Financial transfer execution contract."""

from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class TransferExecutionResult:
    """Immutable result of a financial transfer execution."""

    operation_id: str
    transfer_id: str
    source_account_id: str
    destination_account_id: str
    amount: str
    unit: str
    status: str
    source_uvi_transaction_id: str | None = None
    destination_uvi_transaction_id: str | None = None
    financial_transaction_hash: str | None = None
    metadata: Mapping[str, Any] | None = None
