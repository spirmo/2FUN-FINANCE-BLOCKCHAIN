"""Internal transfer validation."""

from decimal import Decimal, InvalidOperation

from financial_core.internal.contracts import (
    InternalTransferDecision,
    InternalTransferRequest,
)


class InternalTransferValidator:
    """Validate internal transfer requests without mutating state."""

    def validate(
        self,
        request: InternalTransferRequest,
    ) -> InternalTransferDecision:
        if not request.operation_id:
            return InternalTransferDecision(
                request.operation_id,
                False,
                "operation_id is required",
            )

        if not request.source_user_id:
            return InternalTransferDecision(
                request.operation_id,
                False,
                "source_user_id is required",
            )

        if not request.target_user_id:
            return InternalTransferDecision(
                request.operation_id,
                False,
                "target_user_id is required",
            )

        if request.source_user_id == request.target_user_id:
            return InternalTransferDecision(
                request.operation_id,
                False,
                "source and target users must differ",
            )

        if not request.unit:
            return InternalTransferDecision(
                request.operation_id,
                False,
                "unit is required",
            )

        try:
            amount = Decimal(request.amount)
        except (InvalidOperation, ValueError):
            return InternalTransferDecision(
                request.operation_id,
                False,
                "amount must be a valid decimal",
            )

        if amount <= 0:
            return InternalTransferDecision(
                request.operation_id,
                False,
                "amount must be greater than zero",
            )

        return InternalTransferDecision(
            request.operation_id,
            True,
        )
