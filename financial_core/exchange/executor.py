"""Exchange execution."""

from financial_core.exchange.contracts import (
    ExchangeRequest,
    ExchangeResult,
)
from financial_core.exchange.validator import ExchangeValidator
from financial_core.settlement.contracts import SettlementRequest


class ExchangeExecutor:
    """
    Execute an approved exchange request.

    Exchange does not own a ledger or settlement state.
    It produces a SettlementRequest for the existing Settlement domain.
    """

    def __init__(self):
        self._validator = ExchangeValidator()

    def execute(
        self,
        request: ExchangeRequest,
    ) -> ExchangeResult:
        decision = self._validator.validate(request)

        if not decision.approved:
            raise ValueError(decision.reason)

        settlement_request = SettlementRequest(
            operation_id=request.operation_id,
            settlement_type="INTERNAL",
            amount=request.source_amount,
            unit=request.source_unit,
            metadata={
                **dict(request.metadata),
                "exchange_target_unit": request.target_unit,
                "exchange_target_amount": request.quoted_target_amount,
                "exchange_fee_amount": request.fee_amount,
                "settlement_source": "EXCHANGE",
            },
        )

        return ExchangeResult(
            operation_id=request.operation_id,
            source_unit=request.source_unit,
            target_unit=request.target_unit,
            source_amount=request.source_amount,
            target_amount=request.quoted_target_amount,
            fee_amount=request.fee_amount,
            status="READY_FOR_SETTLEMENT",
            settlement_request=settlement_request,
            metadata=dict(request.metadata),
        )
