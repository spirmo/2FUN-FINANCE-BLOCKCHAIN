"""Financial transfer execution through the existing UVI."""

from decimal import Decimal

from financial_core.contracts.transfer import TransferRequest
from financial_core.contracts.transfer_execution import TransferExecutionResult
from financial_core.idempotency.memory_store import InMemoryIdempotencyStore
from financial_core.idempotency.store import IdempotencyStore
from financial_core.operations.transfer_validator import TransferValidator
from platform_core.universal_value.core.contracts import ValueEvent
from platform_core.universal_value.ledger.value_ledger import ValueLedger
from platform_core.universal_value.transactions.transaction_manager import (
    TransactionManager,
)


class TransferExecutor:
    """Execute transfers using the existing UVI ledger."""

    def __init__(
        self,
        ledger: ValueLedger,
        idempotency_store: IdempotencyStore | None = None,
    ):
        self._ledger = ledger
        self._transaction_manager = TransactionManager(ledger)
        self._validator = TransferValidator()
        self._idempotency_store = (
            idempotency_store
            if idempotency_store is not None
            else InMemoryIdempotencyStore()
        )

    def execute(
        self,
        request: TransferRequest,
    ) -> TransferExecutionResult:
        """Execute a transfer with idempotent execution and rollback."""

        validation = self._validator.validate(request)

        if not validation.valid:
            raise ValueError(validation.reason)

        previous_result = self._idempotency_store.get(
            request.operation_id
        )

        if previous_result is not None:
            return previous_result

        amount = Decimal(request.amount)

        source_balance = self._ledger.balance(
            request.source_account_id,
            request.unit,
        )

        if amount > source_balance:
            raise ValueError("Insufficient UVI balance")

        transfer_id = request.operation_id

        source_transaction = self._transaction_manager.create_transaction(
            event=ValueEvent(
                event_id=f"{transfer_id}:debit",
                user_id=request.source_account_id,
                source="2FUNC",
                action="TRANSFER",
                base_value=amount,
                currency=request.unit,
                metadata=dict(request.metadata),
            ),
            amount=amount,
            transaction_type="DEBIT",
            metadata={
                **dict(request.metadata),
                "transfer_id": transfer_id,
                "side": "SOURCE",
            },
        )

        try:
            destination_transaction = (
                self._transaction_manager.create_transaction(
                    event=ValueEvent(
                        event_id=f"{transfer_id}:credit",
                        user_id=request.destination_account_id,
                        source="2FUNC",
                        action="TRANSFER",
                        base_value=amount,
                        currency=request.unit,
                        metadata=dict(request.metadata),
                    ),
                    amount=amount,
                    transaction_type="CREDIT",
                    metadata={
                        **dict(request.metadata),
                        "transfer_id": transfer_id,
                        "side": "DESTINATION",
                    },
                )
            )

        except Exception:
            self._transaction_manager.create_transaction(
                event=ValueEvent(
                    event_id=f"{transfer_id}:rollback",
                    user_id=request.source_account_id,
                    source="2FUNC",
                    action="TRANSFER_ROLLBACK",
                    base_value=amount,
                    currency=request.unit,
                    metadata=dict(request.metadata),
                ),
                amount=amount,
                transaction_type="CREDIT",
                metadata={
                    **dict(request.metadata),
                    "transfer_id": transfer_id,
                    "side": "ROLLBACK",
                    "reason": "DESTINATION_CREDIT_FAILED",
                },
            )
            raise

        result = TransferExecutionResult(
            operation_id=request.operation_id,
            transfer_id=transfer_id,
            source_account_id=request.source_account_id,
            destination_account_id=request.destination_account_id,
            amount=request.amount,
            unit=request.unit,
            status="EXECUTED",
            source_uvi_transaction_id=source_transaction.transaction_id,
            destination_uvi_transaction_id=destination_transaction.transaction_id,
            metadata={
                "authority": "EXISTING_UVI",
                "execution": "UVI_DEBIT_CREDIT",
            },
        )

        self._idempotency_store.save(
            request.operation_id,
            result,
        )

        return result
