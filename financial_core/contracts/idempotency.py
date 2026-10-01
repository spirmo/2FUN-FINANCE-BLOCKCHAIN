"""Generic persistent idempotency contracts."""

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class IdempotencyRecord:
    """Durable result record for any financial operation."""

    operation_id: str
    operation_type: str
    result: Mapping[str, Any]


class GenericIdempotencyStore(Protocol):
    """Generic durable idempotency boundary.

    Idempotency persistence owns execution identity only.
    It does not own financial balances or ledger state.
    """

    def get(self, operation_id: str) -> IdempotencyRecord | None:
        ...

    def save(
        self,
        operation_id: str,
        record: IdempotencyRecord,
    ) -> None:
        ...
