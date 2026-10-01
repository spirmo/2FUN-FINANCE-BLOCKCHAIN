"""End-to-end execution of the existing UVI 2FUNC conversion."""

from decimal import Decimal

from financial_core.contracts.conversion_execution import (
    ConversionExecutionRequest,
    ConversionExecutionResult,
)
from financial_core.contracts.idempotency import IdempotencyRecord
from financial_core.contracts.integrity import IntegrityRequest
from financial_core.idempotency.generic_sqlite_store import (
    GenericSQLiteIdempotencyStore,
)
from financial_core.integrations.integrity_adapter import (
    UniversalIntegrityAdapter,
)

from platform_core.universal_value.core.contracts import ValueEvent
from platform_core.universal_value.ledger.value_ledger import ValueLedger
from platform_core.universal_value.transactions.transaction_manager import (
    TransactionManager,
)
from platform_core.universal_value.twofunc.converter import TwoFuncConverter


class ConversionExecutor:
    """Execute a real UVI conversion with integrity and idempotency.

    Financial balances remain owned by UVI ValueLedger.
    Conversion rules remain owned by UVI TwoFuncConverter.
    Integrity remains owned by Universal Integrity Layer.
    Idempotency owns execution identity only.
    """

    def __init__(
        self,
        ledger: ValueLedger,
        idempotency_store: GenericSQLiteIdempotencyStore,
        integrity_provider: UniversalIntegrityAdapter | None = None,
    ):
        self._ledger = ledger
        self._transaction_manager = TransactionManager(ledger)
        self._idempotency_store = idempotency_store
        self._integrity_provider = (
            integrity_provider or UniversalIntegrityAdapter()
        )
        self._converter = TwoFuncConverter()

    def execute(
        self,
        request: ConversionExecutionRequest,
    ) -> ConversionExecutionResult:
        existing = self._idempotency_store.get(request.operation_id)

        if existing is not None:
            data = existing.result

            return ConversionExecutionResult(
                operation_id=data["operation_id"],
                user_id=data["user_id"],
                status=data["status"],
                source_unit=data["source_unit"],
                target_unit=data["target_unit"],
                source_amount=Decimal(data["source_amount"]),
                target_amount=Decimal(data["target_amount"]),
                remainder_amount=Decimal(data["remainder_amount"]),
                integrity_hash=data["integrity_hash"],
                source_transaction_id=data["source_transaction_id"],
                target_transaction_id=data["target_transaction_id"],
                idempotent=True,
                metadata=dict(data.get("metadata", {})),
            )

        if request.amount <= 0:
            raise ValueError("conversion amount must be positive")

        available = self._ledger.balance(
            request.user_id,
            request.source_unit,
        )

        if available < request.amount:
            raise ValueError(
                "insufficient source balance: "
                f"{available} {request.source_unit}"
            )

        conversion = self._converter.convert(
            request.amount,
            request.source_unit,
            request.target_unit,
        )

        source_consumed = (
            request.amount - conversion.remainder_amount
        )

        if source_consumed <= 0:
            raise ValueError(
                "conversion produces no executable target amount"
            )

        integrity = self._integrity_provider.generate(
            IntegrityRequest(
                operation_id=request.operation_id,
                operation_type="CONVERSION",
                source="FINANCIAL_CORE",
                actor=request.user_id,
                origin="CONVERSION_EXECUTOR",
                target=request.target_unit,
                payload={
                    "source_unit": request.source_unit,
                    "target_unit": request.target_unit,
                    "source_amount": str(request.amount),
                    "source_consumed": str(source_consumed),
                    "target_amount": str(conversion.target_amount),
                    "remainder_amount": str(
                        conversion.remainder_amount
                    ),
                },
                value=str(conversion.target_amount),
            )
        )

        source_event = ValueEvent(
            event_id=f"{request.operation_id}:OUT",
            user_id=request.user_id,
            source="UVI_CONVERSION",
            action="CONVERSION_OUT",
            base_value=source_consumed,
            currency=request.source_unit,
            metadata={
                **dict(request.metadata or {}),
                "operation_id": request.operation_id,
                "target_unit": request.target_unit,
                "target_amount": str(conversion.target_amount),
                "remainder_amount": str(
                    conversion.remainder_amount
                ),
                "integrity_hash": integrity.hash_value,
            },
        )

        source_transaction = self._transaction_manager.create_transaction(
            event=source_event,
            amount=source_consumed,
            transaction_type="CONVERSION_OUT",
            metadata=source_event.metadata,
        )

        target_event = ValueEvent(
            event_id=f"{request.operation_id}:IN",
            user_id=request.user_id,
            source="UVI_CONVERSION",
            action="CONVERSION_IN",
            base_value=conversion.target_amount,
            currency=request.target_unit,
            metadata={
                **dict(request.metadata or {}),
                "operation_id": request.operation_id,
                "source_unit": request.source_unit,
                "source_consumed": str(source_consumed),
                "integrity_hash": integrity.hash_value,
            },
        )

        target_transaction = self._transaction_manager.create_transaction(
            event=target_event,
            amount=conversion.target_amount,
            transaction_type="CONVERSION_IN",
            metadata=target_event.metadata,
        )

        result = ConversionExecutionResult(
            operation_id=request.operation_id,
            user_id=request.user_id,
            status="EXECUTED",
            source_unit=request.source_unit,
            target_unit=request.target_unit,
            source_amount=request.amount,
            target_amount=conversion.target_amount,
            remainder_amount=conversion.remainder_amount,
            integrity_hash=integrity.hash_value,
            source_transaction_id=source_transaction.transaction_id,
            target_transaction_id=target_transaction.transaction_id,
            idempotent=False,
            metadata={
                **dict(request.metadata or {}),
                "integrity_verified": False,
            },
        )

        self._idempotency_store.save(
            request.operation_id,
            IdempotencyRecord(
                operation_id=request.operation_id,
                operation_type="CONVERSION",
                result={
                    "operation_id": result.operation_id,
                    "user_id": result.user_id,
                    "status": result.status,
                    "source_unit": result.source_unit,
                    "target_unit": result.target_unit,
                    "source_amount": str(result.source_amount),
                    "target_amount": str(result.target_amount),
                    "remainder_amount": str(
                        result.remainder_amount
                    ),
                    "integrity_hash": result.integrity_hash,
                    "source_transaction_id": result.source_transaction_id,
                    "target_transaction_id": result.target_transaction_id,
                    "metadata": dict(result.metadata),
                },
            ),
        )

        return result
