"""Financial Core adapter for the central Universal Integrity Layer."""

from financial_core.contracts.integrity import (
    IntegrityProvider,
    IntegrityRequest,
    IntegrityResult,
)
from platform_core.audit.audit_hash_spec import AuditHashSpec


class UniversalIntegrityAdapter(IntegrityProvider):
    """
    Connect Financial Core to the existing central integrity engine.

    Hash generation remains owned by Universal Integrity Layer.
    """

    def generate(
        self,
        request: IntegrityRequest,
    ) -> IntegrityResult:
        operation = {
            "operation_id": request.operation_id,
            "operation_type": request.operation_type,
            "source": request.source,
            "actor": request.actor,
            "origin": request.origin,
            "target": request.target,
            "payload": dict(request.payload),
            "value": request.value,
        }

        hash_value = AuditHashSpec.generate_universal(
            operation,
            request.previous_hash,
        )

        return IntegrityResult(
            operation_id=request.operation_id,
            integrity_version=AuditHashSpec.UNIVERSAL_VERSION,
            hash_value=hash_value,
            previous_hash=request.previous_hash,
            algorithm=AuditHashSpec.HASH_ALGORITHM,
            verified=False,
            metadata={
                "authority": "UNIVERSAL_INTEGRITY_LAYER",
                "hash_owner": "UNIVERSAL_INTEGRITY_LAYER",
            },
        )
