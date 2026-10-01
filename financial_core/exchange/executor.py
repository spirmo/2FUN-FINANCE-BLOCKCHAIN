"""Exchange execution."""

from financial_core.contracts.uvi import UVIValueRequest
from financial_core.exchange.contracts import (
    ExchangeRequest,
    ExchangeResult,
)
from financial_core.exchange.validator import ExchangeValidator
from financial_core.integrations.uvi_exchange_adapter import UVIExchangeAdapter
from financial_core.settlement.contracts import SettlementRequest
from platform_core.universal_value.ledger.value_ledger import ValueLedger


class ExchangeExecutor:
    """
    Execute an approved exchange request.

    Exchange does not own value or settlement state.
    Value conversion is delegated to the existing UVI.
    """

    def __init__(self, ledger: ValueLedger):
        self._validator = ExchangeValidator()
        self._uvi_exchange = UVIExchangeAdapter(ledger)

    def execute(self, request: ExchangeRequest) -> ExchangeResult:
        decision = self._validator.validate(request)

        if not decision.approved:
            raise ValueError(decision.reason)

        uvi_request = UVIValueRequest(
            operation_id=request.operation_id,
            user_id=request.user_id,
            amount=request.source_amount,
            unit=request.source_unit,
            metadata={
                **dict(request.metadata),
                "target_unit": request.target_unit,
                "quoted_target_amount": request.quoted_target_amount,
                "conversion_rate": request.conversion_rate,
                "exchange_fee_amount": request.fee_amount,
                "operation_source": "EXCHANGE",
            },
        )

        uvi_result = self._uvi_exchange.process(
            uvi_request,
            target_unit=request.target_unit,
            quoted_target_amount=request.quoted_target_amount,
            conversion_rate=request.conversion_rate,
        )

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
                "uvi_status": uvi_result.status,
                "uvi_source_transaction_id": uvi_result.metadata.get(
                    "source_transaction_id"
                ),
                "uvi_target_transaction_id": uvi_result.metadata.get(
                    "target_transaction_id"
                ),
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
            metadata={
                **dict(request.metadata),
                "uvi_status": uvi_result.status,
                "uvi_source_transaction_id": uvi_result.metadata.get(
                    "source_transaction_id"
                ),
                "uvi_target_transaction_id": uvi_result.metadata.get(
                    "target_transaction_id"
                ),
            },
        )
