"""Persistent integrity gate contract."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class PersistentIntegrityGateRequest:
    """
    Request to authorize a financial operation using
    a persisted integrity record.

    This contract does not execute the operation.
    """

    operation_id: str
    operation_type: str
    amount: str
    unit: str
    source_account_id: str
    destination_account_id: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class PersistentIntegrityGateResult:
    """
    Result of persistent integrity authorization.
    """

    operation_id: str
    authorized: bool
    reason: str
    integrity_hash: str | None = None
    integrity_version: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


class PersistentIntegrityGate:
    """
    Boundary for authorizing financial execution from
    a persisted and verified integrity record.

    This contract does not own financial state.
    """

    def authorize(
        self,
        request: PersistentIntegrityGateRequest,
    ) -> PersistentIntegrityGateResult:
        raise NotImplementedError
