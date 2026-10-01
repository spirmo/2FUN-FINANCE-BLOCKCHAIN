"""Adapter from transfer idempotency to the generic persistent boundary."""

from financial_core.contracts.idempotency import (
    GenericIdempotencyStore,
    IdempotencyRecord,
)
from financial_core.contracts.transfer_execution import (
    TransferExecutionResult,
)
from financial_core.idempotency.persistent_store import (
    PersistentIdempotencyStore,
)


class GenericTransferIdempotencyAdapter(PersistentIdempotencyStore):
    """
    Adapt the generic idempotency contract to TransferExecutor.

    The generic store owns execution identity only.
    TransferExecutionResult remains the transfer-domain result contract.
    Financial balances remain owned by UVI.
    """

    def __init__(self, store: GenericIdempotencyStore):
        self._store = store

    def get(
        self,
        operation_id: str,
    ) -> TransferExecutionResult | None:
        record = self._store.get(operation_id)

        if record is None:
            return None

        result = record.result

        return TransferExecutionResult(
            operation_id=result["operation_id"],
            transfer_id=result["transfer_id"],
            source_account_id=result["source_account_id"],
            destination_account_id=result["destination_account_id"],
            amount=result["amount"],
            unit=result["unit"],
            status=result["status"],
            source_uvi_transaction_id=result.get(
                "source_uvi_transaction_id"
            ),
            destination_uvi_transaction_id=result.get(
                "destination_uvi_transaction_id"
            ),
            financial_transaction_hash=result.get(
                "financial_transaction_hash"
            ),
            metadata=result.get("metadata"),
        )

    def save(
        self,
        operation_id: str,
        result: TransferExecutionResult,
    ) -> None:
        record = IdempotencyRecord(
            operation_id=result.operation_id,
            operation_type="TRANSFER",
            result={
                "operation_id": result.operation_id,
                "transfer_id": result.transfer_id,
                "source_account_id": result.source_account_id,
                "destination_account_id": result.destination_account_id,
                "amount": result.amount,
                "unit": result.unit,
                "status": result.status,
                "source_uvi_transaction_id": (
                    result.source_uvi_transaction_id
                ),
                "destination_uvi_transaction_id": (
                    result.destination_uvi_transaction_id
                ),
                "financial_transaction_hash": (
                    result.financial_transaction_hash
                ),
                "metadata": dict(result.metadata or {}),
            },
        )

        self._store.save(operation_id, record)
