"""Idempotency execution."""

from financial_core.idempotency.contracts import IdempotencyDecision


class IdempotencyExecutor:
    """
    Track operation IDs and prevent duplicate execution.

    This component owns only idempotency state.
    It does not own value, ledger, settlement, or exchange state.
    """

    def __init__(self):
        self._operation_results: dict[str, str] = {}

    def check(
        self,
        operation_id: str,
    ) -> IdempotencyDecision:
        if not operation_id:
            return IdempotencyDecision(
                operation_id=operation_id,
                accepted=False,
                reason="operation_id is required",
            )

        if operation_id in self._operation_results:
            return IdempotencyDecision(
                operation_id=operation_id,
                accepted=False,
                reason="operation already processed",
            )

        return IdempotencyDecision(
            operation_id=operation_id,
            accepted=True,
        )

    def register(
        self,
        operation_id: str,
        result_reference: str,
    ) -> None:
        if not operation_id:
            raise ValueError("operation_id is required")

        if not result_reference:
            raise ValueError("result_reference is required")

        if operation_id in self._operation_results:
            raise ValueError("operation already processed")

        self._operation_results[operation_id] = result_reference

    def check_and_register(
        self,
        operation_id: str,
    ) -> IdempotencyDecision:
        decision = self.check(operation_id)

        if not decision.accepted:
            return decision

        self.register(
            operation_id,
            result_reference=operation_id,
        )

        return decision

    def result_reference(
        self,
        operation_id: str,
    ) -> str | None:
        return self._operation_results.get(operation_id)
