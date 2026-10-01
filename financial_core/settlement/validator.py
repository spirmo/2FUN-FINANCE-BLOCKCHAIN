"""Settlement validation."""

from decimal import Decimal, InvalidOperation

from financial_core.settlement.contracts import (
    SettlementRequest,
    SettlementDecision,
)


class SettlementValidator:
    """Validate settlement requests without mutating state."""

    ALLOWED_TYPES = {"INTERNAL", "ON_CHAIN"}

    def validate(
        self,
        request: SettlementRequest,
    ) -> SettlementDecision:
        if not request.operation_id:
            return SettlementDecision(
                request.operation_id,
                request.settlement_type,
                False,
                "operation_id is required",
            )

        if request.settlement_type not in self.ALLOWED_TYPES:
            return SettlementDecision(
                request.operation_id,
                request.settlement_type,
                False,
                "unsupported settlement type",
            )

        if not request.unit:
            return SettlementDecision(
                request.operation_id,
                request.settlement_type,
                False,
                "unit is required",
            )

        try:
            amount = Decimal(request.amount)
        except (InvalidOperation, ValueError):
            return SettlementDecision(
                request.operation_id,
                request.settlement_type,
                False,
                "amount must be a valid decimal",
            )

        if amount <= 0:
            return SettlementDecision(
                request.operation_id,
                request.settlement_type,
                False,
                "amount must be greater than zero",
            )

        return SettlementDecision(
            request.operation_id,
            request.settlement_type,
            True,
        )
