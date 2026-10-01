"""Risk and security validation."""

from decimal import Decimal, InvalidOperation

from financial_core.risk.contracts import (
    RiskDecision,
    RiskRequest,
)


class RiskValidator:
    """Apply deterministic risk limits without mutating state."""

    ALLOWED_SETTLEMENT_TYPES = {"INTERNAL", "ON_CHAIN"}

    def __init__(self, max_amount: str = "1000000"):
        self._max_amount = Decimal(max_amount)

        if self._max_amount <= 0:
            raise ValueError("max_amount must be greater than zero")

    def validate(
        self,
        request: RiskRequest,
    ) -> RiskDecision:
        if not request.operation_id:
            return RiskDecision(
                request.operation_id,
                False,
                "operation_id is required",
            )

        if request.settlement_type not in self.ALLOWED_SETTLEMENT_TYPES:
            return RiskDecision(
                request.operation_id,
                False,
                "unsupported settlement type",
            )

        if not request.unit:
            return RiskDecision(
                request.operation_id,
                False,
                "unit is required",
            )

        try:
            amount = Decimal(request.amount)
        except (InvalidOperation, ValueError):
            return RiskDecision(
                request.operation_id,
                False,
                "amount must be a valid decimal",
            )

        if amount <= 0:
            return RiskDecision(
                request.operation_id,
                False,
                "amount must be greater than zero",
            )

        if amount > self._max_amount:
            return RiskDecision(
                request.operation_id,
                False,
                "amount exceeds risk limit",
            )

        return RiskDecision(
            request.operation_id,
            True,
        )
