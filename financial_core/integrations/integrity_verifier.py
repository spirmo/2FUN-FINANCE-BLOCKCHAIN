"""Financial Core adapter for universal integrity verification."""

from financial_core.contracts.integrity_verification import (
    IntegrityVerificationRequest,
    IntegrityVerificationResult,
    IntegrityVerifier,
)
from platform_core.audit.audit_hash_spec import AuditHashSpec


class UniversalIntegrityVerifier(IntegrityVerifier):
    """
    Verify Financial Core integrity records through the central
    Universal Integrity Layer.
    """

    def verify(
        self,
        request: IntegrityVerificationRequest,
    ) -> IntegrityVerificationResult:
        operation = {
            "operation_id": request.operation_id,
            "operation_type": request.operation_type,
            "timestamp": None,
            "source": request.source,
            "actor": request.actor,
            "origin": request.origin,
            "target": request.target,
            "payload": dict(request.payload),
            "value": request.value,
        }

        expected_hash = AuditHashSpec.generate_universal(
            operation,
            request.previous_hash,
        )

        valid = expected_hash == request.hash_value

        return IntegrityVerificationResult(
            operation_id=request.operation_id,
            valid=valid,
            reason="HASH_MATCH" if valid else "HASH_MISMATCH",
            integrity_version=AuditHashSpec.UNIVERSAL_VERSION,
            algorithm=AuditHashSpec.HASH_ALGORITHM,
            hash_value=request.hash_value,
            previous_hash=request.previous_hash,
            metadata={
                "authority": "UNIVERSAL_INTEGRITY_LAYER",
                "verification": "RECOMPUTE_AND_COMPARE",
                "expected_hash": expected_hash,
            },
        )
