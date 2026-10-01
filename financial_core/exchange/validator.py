"""Exchange validation."""

from decimal import Decimal, InvalidOperation

from financial_core.exchange.contracts import (
    ExchangeDecision,
    ExchangeRequest,
)


class ExchangeValidator:
    """Validate exchange requests without mutating financial state."""

    def validate(
        self,
        request: ExchangeRequest,
    ) -> ExchangeDecision:
        if not request.operation_id:
            return ExchangeDecision(
                request.operation_id,
                False,
                "operation_id is required",
            )

        if not request.source_unit:
            return ExchangeDecision(
                request.operation_id,
                False,
                "source_unit is required",
            )

        if not request.target_unit:
            return ExchangeDecision(
                request.operation_id,
                False,
                "target_unit is required",
            )

        if request.source_unit == request.target_unit:
            return ExchangeDecision(
                request.operation_id,
                False,
                "source and target units must differ",
            )

        try:
            source_amount = Decimal(request.source_amount)
            target_amount = Decimal(request.quoted_target_amount)
            fee_amount = Decimal(request.fee_amount)
        except (InvalidOperation, ValueError):
            return ExchangeDecision(
                request.operation_id,
                False,
                "amounts must be valid decimals",
            )

        if source_amount <= 0:
            return ExchangeDecision(
                request.operation_id,
                False,
                "source_amount must be greater than zero",
            )

        if target_amount <= 0:
            return ExchangeDecision(
                request.operation_id,
                False,
                "quoted_target_amount must be greater than zero",
            )

        if fee_amount < 0:
            return ExchangeDecision(
                request.operation_id,
                False,
                "fee_amount cannot be negative",
            )

        return ExchangeDecision(
            request.operation_id,
            True,
        )
