"""Financial operation integrity contracts."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class OperationIntegrityRequest:
    """
    Integrity request derived from a financial operation.

    This contract does not execute the financial operation and does not
    mutate any ledger or account state.
    """

    operation_id: str
    operation_type: str
    user_id: str
    source: str
    target: str | None
    amount: str
    unit: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class OperationIntegrityResult:
    """
    Integrity result associated with a financial operation.
    """

    operation_id: str
    operation_type: str
    integrity_version: str
    algorithm: str
    hash_value: str
    previous_hash: str
    authority: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
