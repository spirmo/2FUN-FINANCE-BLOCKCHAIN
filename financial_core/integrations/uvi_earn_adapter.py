"""Executable EARN adapter for the existing 2FUN-OS UVI."""

from decimal import Decimal
from platform_core.universal_value.unit_contract import canonicalize_unit

from financial_core.contracts.uvi import (
    UVIValueRequest,
    UVIValueResult,
)
from platform_core.universal_value.core.contracts import ValueEvent
from platform_core.universal_value.ledger.value_ledger import ValueLedger
from platform_core.universal_value.transactions.transaction_manager import (
    TransactionManager,
)


class UVIEarnAdapter:
    """Execute EARN operations through the existing UVI."""

    def __init__(self, ledger: ValueLedger):
        self._ledger = ledger
        self._transaction_manager = TransactionManager(ledger)

    def process(self, request: UVIValueRequest) -> UVIValueResult:
        if not request.operation_id or not request.user_id:
            raise ValueError("operation_id and user_id are required")

        amount = Decimal(request.amount)
        if not amount.is_finite() or amount < 0:
            raise ValueError("EARN amount must be finite and non-negative")

        existing = [
            entry for entry in self._ledger.all_entries()
            if entry.event_id == request.operation_id
        ]

        if existing:
            if len(existing) != 1:
                raise ValueError("operation_id has multiple existing ledger entries")

            entry = existing[0]
            metadata = dict(getattr(entry, "metadata", {}) or {})
            same_operation = (
                entry.user_id == request.user_id
                and Decimal(str(entry.amount)) == amount
                and canonicalize_unit(entry.currency)
                == canonicalize_unit(request.unit)
                and entry.transaction_type == "EARN"
                and metadata.get("financial_core_operation_id") == request.operation_id
            )
            if not same_operation:
                raise ValueError(
                    "operation_id already recorded with different EARN parameters"
                )

            return UVIValueResult(
                operation_id=request.operation_id,
                status="RECORDED",
                recorded=True,
                metadata={
                    "authority": "EXISTING_UVI",
                    "transaction_id": entry.transaction_id,
                    "unit": request.unit,
                    "idempotent_replay": True,
                },
            )

        event = ValueEvent(
            event_id=request.operation_id,
            user_id=request.user_id,
            source="2FUNC",
            action="EARN",
            base_value=amount,
            currency=request.unit,
            metadata=dict(request.metadata),
        )
        transaction = self._transaction_manager.create_transaction(
            event=event,
            amount=amount,
            transaction_type="EARN",
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
                "idempotent_replay": False,
            },
        )
