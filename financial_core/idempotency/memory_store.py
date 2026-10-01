"""In-memory idempotency state store."""

from financial_core.contracts.transfer_execution import TransferExecutionResult


class InMemoryIdempotencyStore:
    """Temporary in-memory store for operation execution results."""

    def __init__(self) -> None:
        self._results: dict[str, TransferExecutionResult] = {}

    def get(
        self,
        operation_id: str,
    ) -> TransferExecutionResult | None:
        return self._results.get(operation_id)

    def save(
        self,
        operation_id: str,
        result: TransferExecutionResult,
    ) -> None:
        if operation_id in self._results:
            raise ValueError(
                f"Operation already recorded: {operation_id}"
            )

        self._results[operation_id] = result
