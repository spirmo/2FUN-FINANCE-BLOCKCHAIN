"""Accounting integrity contract."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class AccountingIntegrityRequest:
    entry_id: str
    operation_id: str
    account_id: str
    entry_type: str
    amount: str
    unit: str
    direction: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class AccountingIntegrityResult:
    entry_id: str
    operation_id: str
    integrity_version: str
    algorithm: str
    hash_value: str
    previous_hash: str
    authority: str
    verified: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


class AccountingIntegrityProvider:
    def generate(
        self,
        request: AccountingIntegrityRequest,
        previous_hash: str = "GENESIS",
    ) -> AccountingIntegrityResult:
        raise NotImplementedError
