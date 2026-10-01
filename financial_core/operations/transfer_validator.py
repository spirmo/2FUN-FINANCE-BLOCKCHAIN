"""Financial transfer validation."""

from decimal import Decimal, InvalidOperation

from financial_core.contracts.transfer import (
    TransferRequest,
    TransferValidationResult,
)


class TransferValidator:
    """Validate transfer requests without mutating financial state."""

    def validate(
        self,
        request: TransferRequest,
    ) -> TransferValidationResult:
        """Validate the transfer request."""

        if not request.operation_id:
            return TransferValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="operation_id is required",
            )

        if not request.source_account_id:
            return TransferValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="source_account_id is required",
            )

        if not request.destination_account_id:
            return TransferValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="destination_account_id is required",
            )

        if request.source_account_id == request.destination_account_id:
            return TransferValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="source and destination accounts must differ",
            )

        try:
            amount = Decimal(request.amount)
        except (InvalidOperation, ValueError):
            return TransferValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="amount must be numeric",
            )

        if amount <= 0:
            return TransferValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="amount must be positive",
            )

        if not request.unit:
            return TransferValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="unit is required",
            )

        return TransferValidationResult(
            operation_id=request.operation_id,
            valid=True,
        )
