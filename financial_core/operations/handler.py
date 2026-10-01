"""Financial operation execution boundary."""

from financial_core.contracts.execution import FinancialExecutionResult
from financial_core.contracts.operation import FinancialOperationRequest


class FinancialOperationHandler:
    """Prepare a financial operation for execution."""

    def execute(
        self,
        request: FinancialOperationRequest,
    ) -> FinancialExecutionResult:
        """Execute the operation boundary without owning external state."""

        return FinancialExecutionResult(
            operation_id=request.operation_id,
            status="EXECUTED",
            value_recorded=False,
            settlement_required=request.operation_type
            in {
                "TRANSFER",
                "PAYMENT",
                "EXCHANGE",
                "STAKE",
                "LEND",
                "BORROW",
                "LIQUIDITY",
                "SETTLEMENT",
            },
            settlement_type=(
                "BLOCKCHAIN"
                if request.operation_type in {
                    "STAKE",
                    "LIQUIDITY",
                }
                else "INTERNAL"
            ),
            metadata={
                "operation_type": request.operation_type,
                "execution_mode": "BOUNDARY_ONLY",
            },
        )
