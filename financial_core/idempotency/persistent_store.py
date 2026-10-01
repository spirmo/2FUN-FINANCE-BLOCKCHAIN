"""Persistent idempotency store contract."""

from typing import Protocol

from financial_core.contracts.transfer_execution import (
    TransferExecutionResult,
)


class PersistentIdempotencyStore(Protocol):
    """
    Durable idempotency boundary.

    Implementations must preserve operation results across
    process restarts without becoming an authority for financial state.
    """

    def get(self, operation_id: str) -> TransferExecutionResult | None:
        ...

    def save(
        self,
        operation_id: str,
        result: TransferExecutionResult,
    ) -> None:
        ...
