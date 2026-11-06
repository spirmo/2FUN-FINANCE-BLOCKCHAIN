"""Internal transfer execution."""

from decimal import Decimal

from financial_core.internal.contracts import (
    InternalTransferRecord,
    InternalTransferRequest,
)
from financial_core.internal.validator import InternalTransferValidator
from platform_core.universal_value.ledger.value_ledger import ValueLedger


class InternalTransferExecutor:
    """
    Execute an internal value transfer through the existing UVI ledger.

    Internal transfer does not create a second value ledger.
    """

    def __init__(self, ledger: ValueLedger):
        self._validator = InternalTransferValidator()
        self._ledger = ledger

    def execute(
        self,
        request: InternalTransferRequest,
    ) -> InternalTransferRecord:
        decision = self._validator.validate(request)

        if not decision.approved:
            raise ValueError(decision.reason)

        amount = Decimal(request.amount)

        transfer = self._ledger.execute_transfer(
            operation_id=request.operation_id,
            source_user_id=request.source_user_id,
            destination_user_id=request.target_user_id,
            amount=amount,
            currency=request.unit,
            metadata={
                **dict(request.metadata),
                "source": "INTERNAL",
                "financial_core_operation_id": request.operation_id,
            },
        )

        return InternalTransferRecord(
            operation_id=request.operation_id,
            source_user_id=request.source_user_id,
            target_user_id=request.target_user_id,
            amount=request.amount,
            unit=request.unit,
            status="TRANSFERRED",
            source_transaction_id=transfer["debit_transaction_id"],
            target_transaction_id=transfer["credit_transaction_id"],
            metadata={
                **dict(request.metadata),
                "authority": "EXISTING_UVI",
            },
        )
