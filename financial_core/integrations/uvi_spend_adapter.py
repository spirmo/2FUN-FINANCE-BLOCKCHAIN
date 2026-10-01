"""Executable SPEND adapter for the existing 2FUN-OS UVI."""

from decimal import Decimal

from financial_core.contracts.uvi import (
    UVIValueRequest,
    UVIValueResult,
)
from platform_core.universal_value.core.contracts import ValueEvent
from platform_core.universal_value.ledger.value_ledger import ValueLedger
from platform_core.universal_value.transactions.transaction_manager import (
    TransactionManager,
)


class UVISpendAdapter:
    """Execute SPEND operations through the existing UVI."""

    def __init__(self, ledger: ValueLedger):
        self._ledger = ledger
        self._transaction_manager = TransactionManager(ledger)

    def process(self, request: UVIValueRequest) -> UVIValueResult:
        """Record a SPEND operation through the existing UVI."""

        amount = Decimal(request.amount)

        if amount <= 0:
            raise ValueError("SPEND amount must be positive")

        balance = self._ledger.balance(
            user_id=request.user_id,
            currency=request.unit,
        )

        if amount > balance:
            raise ValueError("Insufficient UVI balance")

        event = ValueEvent(
            event_id=request.operation_id,
            user_id=request.user_id,
            source="2FUNC",
            action="SPEND",
            base_value=amount,
            currency=request.unit,
            metadata=dict(request.metadata),
        )

        transaction = self._transaction_manager.create_transaction(
            event=event,
            amount=amount,
            transaction_type="SPEND",
            metadata={
                **dict(request.metadata),
                "financial_core_operation_id": request.operation_id,
                "unit": request.unit,
            },
        )

        return UVIValueResult(
            operation_id=request.operation_id,
            status="RECORDED",
            recorded=True,
            metadata={
                "authority": "EXISTING_UVI",
                "transaction_id": transaction.transaction_id,
                "unit": request.unit,
            },
        )
