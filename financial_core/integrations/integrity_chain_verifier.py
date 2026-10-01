"""Financial Core adapter for universal integrity chain verification."""

from financial_core.contracts.integrity_chain import (
    IntegrityChainVerificationRequest,
    IntegrityChainVerificationResult,
    IntegrityChainVerifier,
)
from platform_core.audit.audit_hash_spec import AuditHashSpec


class UniversalIntegrityChainVerifier(IntegrityChainVerifier):
    """
    Verify Financial Core integrity chains through the central
    Universal Integrity Layer.
    """

    def verify(
        self,
        request: IntegrityChainVerificationRequest,
    ) -> IntegrityChainVerificationResult:
        records = [dict(record) for record in request.records]
        total = len(records)

        if not records:
            return IntegrityChainVerificationResult(
                valid=True,
                reason="CHAIN_OK",
                total=0,
                metadata={
                    "authority": "UNIVERSAL_INTEGRITY_LAYER",
                    "verification": "CENTRAL_CHAIN_VERIFIER",
                },
            )

        if request.previous_hash != AuditHashSpec.GENESIS:
            return IntegrityChainVerificationResult(
                valid=False,
                reason="UNSUPPORTED_CHAIN_ROOT",
                total=total,
                metadata={
                    "authority": "UNIVERSAL_INTEGRITY_LAYER",
                    "verification": "CENTRAL_CHAIN_VERIFIER",
                    "expected_root": AuditHashSpec.GENESIS,
                    "actual_root": request.previous_hash,
                },
            )

        result = AuditHashSpec.verify_universal_chain(records)

        failed_index = result.get("index")

        return IntegrityChainVerificationResult(
            valid=result["valid"],
            reason=result["reason"],
            total=total,
            failed_index=failed_index,
            metadata={
                "authority": "UNIVERSAL_INTEGRITY_LAYER",
                "verification": "CENTRAL_CHAIN_VERIFIER",
            },
        )
