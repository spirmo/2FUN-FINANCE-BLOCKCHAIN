"""Internal transfer execution."""

from decimal import Decimal

from financial_core.internal.contracts import (
    InternalTransferRecord,
    InternalTransferRequest,
)
from financial_core.internal.validator import InternalTransferValidator
from platform_core.universal_value.core.contracts import ValueEvent
from platform_core.universal_value.ledger.value_ledger import ValueLedger
from platform_core.universal_value.transactions.transaction_manager import (
    TransactionManager,
)


class InternalTransferExecutor:
    """
    Execute an internal value transfer through the existing UVI ledger.

    Internal transfer does not create a second value ledger.
    """

    def __init__(self, ledger: ValueLedger):
        self._validator = InternalTransferValidator()
        self._ledger = ledger
        self._transaction_manager = TransactionManager(ledger)

    def execute(
        self,
        request: InternalTransferRequest,
    ) -> InternalTransferRecord:
        decision = self._validator.validate(request)

        if not decision.approved:
            raise ValueError(decision.reason)

        amount = Decimal(request.amount)

        if self._ledger.balance(
            request.source_user_id,
            request.unit,
        ) < amount:
            raise ValueError("insufficient UVI balance")

        source_event = ValueEvent(
            event_id=f"{request.operation_id}:OUT",
            user_id=request.source_user_id,
            source="INTERNAL",
            action="INTERNAL_TRANSFER_OUT",
            base_value=amount,
            currency=request.unit,
            metadata=dict(request.metadata),
        )

        source_transaction = self._transaction_manager.create_transaction(
            event=source_event,
            amount=amount,
            transaction_type="SPEND",
            metadata={
                **dict(request.metadata),
                "financial_core_operation_id": request.operation_id,
                "transfer_side": "SOURCE",
                "target_user_id": request.target_user_id,
                "unit": request.unit,
            },
        )

        target_event = ValueEvent(
            event_id=f"{request.operation_id}:IN",
            user_id=request.target_user_id,
            source="INTERNAL",
            action="INTERNAL_TRANSFER_IN",
            base_value=amount,
            currency=request.unit,
            metadata=dict(request.metadata),
        )

        target_transaction = self._transaction_manager.create_transaction(
            event=target_event,
            amount=amount,
            transaction_type="CREDIT",
            metadata={
                **dict(request.metadata),
                "financial_core_operation_id": request.operation_id,
                "transfer_side": "TARGET",
                "source_user_id": request.source_user_id,
                "unit": request.unit,
            },
        )

        return InternalTransferRecord(
            operation_id=request.operation_id,
            source_user_id=request.source_user_id,
            target_user_id=request.target_user_id,
            amount=request.amount,
            unit=request.unit,
            status="TRANSFERRED",
            source_transaction_id=source_transaction.transaction_id,
            target_transaction_id=target_transaction.transaction_id,
            metadata={
                **dict(request.metadata),
                "authority": "EXISTING_UVI",
            },
        )
