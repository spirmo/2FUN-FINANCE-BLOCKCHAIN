"""Financial account state contract."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class FinancialAccountState:
    """
    Financial account state read model.

    Account identity/status belong to Financial Core.
    Value balance remains authoritative in UVI.
    """

    account_id: str
    owner_id: str
    account_type: str
    status: str
    unit: str
    balance: str
    value_authority: str = "EXISTING_UVI"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FinancialAccountStateRequest:
    """Request to read financial account state."""

    account_id: str
    unit: str
