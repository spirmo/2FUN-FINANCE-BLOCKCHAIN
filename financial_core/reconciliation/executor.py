"""Reconciliation execution."""

from financial_core.reconciliation.contracts import (
    ReconciliationDecision,
    ReconciliationRequest,
)
from financial_core.reconciliation.validator import ReconciliationValidator


class ReconciliationExecutor:
    """
    Execute reconciliation checks.

    Reconciliation detects discrepancies but does not mutate
    value, ledger, settlement, or exchange state.
    """

    def __init__(self):
        self._validator = ReconciliationValidator()

    def reconcile(
        self,
        request: ReconciliationRequest,
    ) -> ReconciliationDecision:
        return self._validator.validate(request)
