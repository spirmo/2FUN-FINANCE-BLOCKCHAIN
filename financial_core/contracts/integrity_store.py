"""Persistent integrity record contract."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class IntegrityRecord:
    operation_id: str
    operation_type: str
    integrity_version: str
    algorithm: str
    hash_value: str
    previous_hash: str
    source: str
    actor: str | None = None
    origin: str | None = None
    target: str | None = None


class IntegrityRecordStore(Protocol):
    """
    Persistent storage boundary for integrity records.

    This store does not own financial balances,
    transactions, or blockchain state.
    """

    def get(self, operation_id: str) -> IntegrityRecord | None:
        ...

    def save(self, record: IntegrityRecord) -> None:
        ...
