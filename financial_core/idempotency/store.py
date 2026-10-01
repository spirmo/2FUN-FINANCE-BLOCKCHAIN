"""Idempotency state store contract."""

from typing import Protocol

from financial_core.contracts.transfer_execution import TransferExecutionResult


class IdempotencyStore(Protocol):
    """Authoritative boundary for operation execution identity."""

    def get(self, operation_id: str) -> TransferExecutionResult | None:
        """Return the previously recorded execution result, if present."""
        ...

    def save(
        self,
        operation_id: str,
        result: TransferExecutionResult,
    ) -> None:
        """Record an execution result for an operation."""
        ...
