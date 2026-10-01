"""Generate universal integrity records for accounting entries."""

from financial_core.contracts.accounting_integrity import (
    AccountingIntegrityRequest,
    AccountingIntegrityResult,
)
from financial_core.contracts.integrity import IntegrityRequest
from financial_core.integrations.integrity_adapter import UniversalIntegrityAdapter


class AccountingIntegrityAdapter:
    """Bridges Accounting entries to the Universal Integrity Layer."""

    def __init__(self):
        self._integrity = UniversalIntegrityAdapter()

    def generate(
        self,
        request: AccountingIntegrityRequest,
        previous_hash: str = "GENESIS",
    ) -> AccountingIntegrityResult:

        integrity_result = self._integrity.generate(
            IntegrityRequest(
                operation_id=request.operation_id,
                operation_type=f"ACCOUNTING_{request.entry_type}",
                source="ACCOUNTING",
                actor=request.account_id,
                origin="FINANCIAL_CORE",
                target=request.account_id,
                payload={
                    "entry_id": request.entry_id,
                    "account_id": request.account_id,
                    "amount": request.amount,
                    "unit": request.unit,
                    "direction": request.direction,
                    **dict(request.metadata),
                },
                value=request.amount,
                previous_hash=previous_hash,
            )
        )

        return AccountingIntegrityResult(
            entry_id=request.entry_id,
            operation_id=request.operation_id,
            integrity_version=integrity_result.integrity_version,
            algorithm=integrity_result.algorithm,
            hash_value=integrity_result.hash_value,
            previous_hash=integrity_result.previous_hash,
            authority="UNIVERSAL_INTEGRITY_LAYER",
            verified=integrity_result.verified,
        )
