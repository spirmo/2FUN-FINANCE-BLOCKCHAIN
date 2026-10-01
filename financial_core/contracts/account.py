"""Financial account boundary contract."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class FinancialAccount:
    """Immutable identity and ownership boundary of a financial account."""

    account_id: str
    owner_id: str
    account_type: str
    status: str = "ACTIVE"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AccountTransferRequest:
    """Immutable request describing an account-to-account transfer."""

    operation_id: str
    source_account_id: str
    destination_account_id: str
    amount: str
    unit: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
