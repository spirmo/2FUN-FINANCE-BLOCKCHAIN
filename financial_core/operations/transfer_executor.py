"""Financial transfer execution through the existing UVI."""

from decimal import Decimal

from financial_core.contracts.transfer import TransferRequest
from financial_core.contracts.integrity import IntegrityRequest
from financial_core.contracts.transfer_execution import TransferExecutionResult
from financial_core.idempotency.memory_store import InMemoryIdempotencyStore
from financial_core.integrations.integrity_adapter import UniversalIntegrityAdapter
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
        integrity_provider: UniversalIntegrityAdapter | None = None,
    ):
        self._ledger = ledger
        self._transaction_manager = TransactionManager(ledger)
        self._validator = TransferValidator()
        self._idempotency_store = (
            idempotency_store
            if idempotency_store is not None
            else InMemoryIdempotencyStore()
        )
        self._integrity_provider = (
            integrity_provider
            if integrity_provider is not None
            else UniversalIntegrityAdapter()
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

        transfer = self._ledger.execute_transfer(
            operation_id=request.operation_id,
            source_user_id=request.source_account_id,
            destination_user_id=request.destination_account_id,
            amount=amount,
            currency=request.unit,
            metadata=dict(request.metadata),
        )

        integrity = self._integrity_provider.generate(
            IntegrityRequest(
                operation_id=request.operation_id,
                operation_type="TRANSFER",
                source="FINANCIAL_CORE",
                actor=request.source_account_id,
                origin="TRANSFER_EXECUTOR",
                target=request.destination_account_id,
                payload={
                    "transfer_id": request.operation_id,
                    "source_account_id": request.source_account_id,
                    "destination_account_id": request.destination_account_id,
                    "amount": request.amount,
                    "unit": request.unit,
                    "source_uvi_transaction_id": transfer["debit_transaction_id"],
                    "destination_uvi_transaction_id": transfer["credit_transaction_id"],
                },
                value=request.amount,
                previous_hash="GENESIS",
            )
        )

        result = TransferExecutionResult(
            operation_id=request.operation_id,
            transfer_id=request.operation_id,
            source_account_id=request.source_account_id,
            destination_account_id=request.destination_account_id,
            amount=request.amount,
            unit=request.unit,
            status="EXECUTED",
            source_uvi_transaction_id=transfer["debit_transaction_id"],
            destination_uvi_transaction_id=transfer["credit_transaction_id"],
            financial_transaction_hash=integrity.hash_value,
            metadata={
                "authority": "UNIVERSAL_INTEGRITY_LAYER",
                "execution": "UVI_DEBIT_CREDIT",
                "integrity_version": integrity.integrity_version,
            },
        )

        self._idempotency_store.save(
            request.operation_id,
            result,
        )

        return result
