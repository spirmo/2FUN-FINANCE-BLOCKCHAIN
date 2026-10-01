"""Persistent integrity gate implementation."""

from financial_core.contracts.integrity_store import IntegrityRecord
from financial_core.contracts.integrity_verification import (
    IntegrityVerificationRequest,
)
from financial_core.contracts.persistent_integrity_gate import (
    PersistentIntegrityGate,
    PersistentIntegrityGateRequest,
    PersistentIntegrityGateResult,
)
from financial_core.integrity.sqlite_store import (
    SQLiteIntegrityRecordStore,
)
from financial_core.integrations.integrity_verifier import (
    UniversalIntegrityVerifier,
)


class SQLitePersistentIntegrityGate(PersistentIntegrityGate):
    """
    Authorizes financial execution using a persisted
    and successfully verified integrity record.

    This component does not own financial state.
    """

    def __init__(self, store: SQLiteIntegrityRecordStore):
        self._store = store
        self._verifier = UniversalIntegrityVerifier()

    def authorize(
        self,
        request: PersistentIntegrityGateRequest,
    ) -> PersistentIntegrityGateResult:

        record = self._store.get(request.operation_id)

        if record is None:
            return PersistentIntegrityGateResult(
                operation_id=request.operation_id,
                authorized=False,
                reason="INTEGRITY_RECORD_NOT_FOUND",
            )

        verification = self._verifier.verify(
            IntegrityVerificationRequest(
                operation_id=record.operation_id,
                operation_type=record.operation_type,
                source=record.source,
                actor=record.actor,
                origin=record.origin,
                target=record.target,
                payload={
                    "amount": request.amount,
                    "unit": request.unit,
                    **dict(request.metadata),
                },
                value=request.amount,
                previous_hash=record.previous_hash,
                hash_value=record.hash_value,
            )
        )

        if not verification.valid:
            return PersistentIntegrityGateResult(
                operation_id=request.operation_id,
                authorized=False,
                reason=verification.reason,
                integrity_hash=record.hash_value,
                integrity_version=record.integrity_version,
            )

        return PersistentIntegrityGateResult(
            operation_id=request.operation_id,
            authorized=True,
            reason=verification.reason,
            integrity_hash=record.hash_value,
            integrity_version=record.integrity_version,
        )
