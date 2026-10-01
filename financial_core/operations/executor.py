"""Financial Core execution coordinator."""

from financial_core.contracts.execution import FinancialExecutionResult
from financial_core.contracts.operation import FinancialOperationRequest
from financial_core.contracts.uvi import UVIValueRequest
from financial_core.integrations.uvi_earn_adapter import UVIEarnAdapter
from financial_core.integrations.uvi_spend_adapter import UVISpendAdapter
from platform_core.universal_value.ledger.value_ledger import ValueLedger


class FinancialOperationExecutor:
    """Execute supported Financial Core operations."""

    def __init__(self, ledger: ValueLedger):
        self._uvi_earn = UVIEarnAdapter(ledger)
        self._uvi_spend = UVISpendAdapter(ledger)

    def execute(
        self,
        request: FinancialOperationRequest,
    ) -> FinancialExecutionResult:
        """Execute an operation through its authoritative subsystem."""

        uvi_request = UVIValueRequest(
            operation_id=request.operation_id,
            user_id=request.user_id,
            amount=request.amount,
            unit=request.unit,
            metadata=request.metadata,
        )

        if request.operation_type == "EARN":
            result = self._uvi_earn.process(uvi_request)

        elif request.operation_type == "SPEND":
            result = self._uvi_spend.process(uvi_request)

        else:
            raise ValueError(
                f"Execution not implemented for: "
                f"{request.operation_type}"
            )

        return FinancialExecutionResult(
            operation_id=request.operation_id,
            status="EXECUTED",
            value_recorded=result.recorded,
            settlement_required=False,
            metadata={
                "authority": "EXISTING_UVI",
                "operation_type": request.operation_type,
                "transaction_id": result.metadata["transaction_id"],
            },
        )
