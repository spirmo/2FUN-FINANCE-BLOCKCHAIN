"""Reconciliation validation."""

from decimal import Decimal, InvalidOperation

from financial_core.reconciliation.contracts import (
    ReconciliationDecision,
    ReconciliationRequest,
)


class ReconciliationValidator:
    """Compare expected and recorded values without mutating state."""

    def validate(
        self,
        request: ReconciliationRequest,
    ) -> ReconciliationDecision:
        if not request.operation_id:
            return ReconciliationDecision(
                request.operation_id,
                "REJECTED",
                "0",
                "operation_id is required",
            )

        if not request.unit:
            return ReconciliationDecision(
                request.operation_id,
                "REJECTED",
                "0",
                "unit is required",
            )

        try:
            expected = Decimal(request.expected_amount)
            recorded = Decimal(request.recorded_amount)
        except (InvalidOperation, ValueError):
            return ReconciliationDecision(
                request.operation_id,
                "REJECTED",
                "0",
                "amounts must be valid decimals",
            )

        difference = recorded - expected

        if difference == 0:
            return ReconciliationDecision(
                request.operation_id,
                "MATCHED",
                "0",
            )

        return ReconciliationDecision(
            request.operation_id,
            "MISMATCH",
            str(difference),
            "expected and recorded amounts differ",
        )
