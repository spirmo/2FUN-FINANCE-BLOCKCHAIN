from financial_core.contracts.integrity_verification import (
    IntegrityVerificationRequest,
)
from financial_core.contracts.operation_integrity import (
    OperationIntegrityResult,
)
from financial_core.integrations.integrity_verifier import (
    UniversalIntegrityVerifier,
)


class FinancialOperationIntegrityVerifier:
    """
    Verifies the integrity of a financial operation
    through the central Universal Integrity Layer.

    Verification is read-only and does not mutate financial state.
    """

    def __init__(self):
        self._verifier = UniversalIntegrityVerifier()

    def verify(
        self,
        operation: OperationIntegrityResult,
        source: str,
        actor: str,
        target: str | None,
        amount: str,
        unit: str,
        metadata: dict | None = None,
    ):
        verification_request = IntegrityVerificationRequest(
            operation_id=operation.operation_id,
            operation_type=operation.operation_type,
            source=source,
            actor=actor,
            origin="FINANCIAL_CORE",
            target=target,
            payload={
                "amount": amount,
                "unit": unit,
                **(metadata or {}),
            },
            value=amount,
            previous_hash=operation.previous_hash,
            hash_value=operation.hash_value,
        )

        return self._verifier.verify(verification_request)
