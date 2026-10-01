"""Integrity-gated transfer execution contract."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class IntegrityGatedTransferRequest:
    """
    Transfer request that requires a verified integrity record
    before execution.

    This contract does not mutate UVI or account state.
    """

    operation_id: str
    source_account_id: str
    destination_account_id: str
    amount: str
    unit: str
    integrity_hash: str
    integrity_version: str = "v3"
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class IntegrityGatedTransferResult:
    """
    Result of an integrity-gated transfer execution.
    """

    operation_id: str
    transfer_id: str
    status: str
    integrity_hash: str
    integrity_verified: bool
    source_uvi_transaction_id: str | None = None
    destination_uvi_transaction_id: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
