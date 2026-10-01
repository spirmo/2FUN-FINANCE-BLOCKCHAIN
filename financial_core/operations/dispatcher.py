"""Financial Core operation dispatcher.

The dispatcher routes validated operation requests without owning
value calculation, ledger state, account state, or blockchain state.
"""

from financial_core.contracts.operation import (
    FinancialOperationRequest,
    FinancialOperationResult,
)


SUPPORTED_OPERATIONS = frozenset(
    {
        "EARN",
        "SPEND",
        "TRANSFER",
        "CONVERT",
        "DEPOSIT",
        "WITHDRAW",
        "PAYMENT",
        "EXCHANGE",
        "STAKE",
        "LEND",
        "BORROW",
        "LIQUIDITY",
        "SETTLEMENT",
    }
)


class OperationDispatcher:
    """Route Financial Core operation requests."""

    def dispatch(
        self,
        request: FinancialOperationRequest,
    ) -> FinancialOperationResult:
        """Validate and route an operation request."""

        if request.operation_type not in SUPPORTED_OPERATIONS:
            raise ValueError(
                f"Unsupported financial operation: "
                f"{request.operation_type}"
            )

        return FinancialOperationResult(
            operation_id=request.operation_id,
            status="ROUTED",
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
            metadata={
                "operation_type": request.operation_type,
                "execution": "NOT_EXECUTED",
            },
        )
