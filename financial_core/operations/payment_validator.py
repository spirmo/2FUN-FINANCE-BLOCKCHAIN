"""Financial payment validation."""

from decimal import Decimal, InvalidOperation

from financial_core.contracts.payment import (
    PaymentRequest,
    PaymentValidationResult,
)


class PaymentValidator:
    """Validate payment requests without mutating financial state."""

    def validate(
        self,
        request: PaymentRequest,
    ) -> PaymentValidationResult:
        if not request.operation_id:
            return PaymentValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="operation_id is required",
            )

        if not request.payer_account_id:
            return PaymentValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="payer_account_id is required",
            )

        if not request.payee_account_id:
            return PaymentValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="payee_account_id is required",
            )

        if request.payer_account_id == request.payee_account_id:
            return PaymentValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="payer and payee must be different",
            )

        if not request.unit:
            return PaymentValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="unit is required",
            )

        try:
            amount = Decimal(request.amount)
        except (InvalidOperation, ValueError):
            return PaymentValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="amount must be a valid decimal",
            )

        if amount <= 0:
            return PaymentValidationResult(
                operation_id=request.operation_id,
                valid=False,
                reason="amount must be greater than zero",
            )

        return PaymentValidationResult(
            operation_id=request.operation_id,
            valid=True,
        )
