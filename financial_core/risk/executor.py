"""Risk gate execution."""

from financial_core.risk.contracts import (
    RiskDecision,
    RiskRequest,
)
from financial_core.risk.validator import RiskValidator


class RiskExecutor:
    """
    Execute deterministic risk validation.

    Risk evaluation does not mutate value, settlement, or ledger state.
    """

    def __init__(self, max_amount: str = "1000000"):
        self._validator = RiskValidator(max_amount=max_amount)

    def evaluate(
        self,
        request: RiskRequest,
    ) -> RiskDecision:
        return self._validator.validate(request)
