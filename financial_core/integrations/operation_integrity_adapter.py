from financial_core.contracts.operation_integrity import (
    OperationIntegrityRequest,
    OperationIntegrityResult,
)
from financial_core.contracts.integrity import IntegrityRequest
from financial_core.integrations.integrity_adapter import (
    UniversalIntegrityAdapter,
)


class FinancialOperationIntegrityAdapter:
    """
    Connects a financial operation to the central Universal Integrity Layer.

    This adapter generates integrity metadata only.
    It does not mutate UVI, account state, settlement state, or blockchain state.
    """

    def __init__(self):
        self._integrity = UniversalIntegrityAdapter()

    def generate(
        self,
        request: OperationIntegrityRequest,
        previous_hash: str = "GENESIS",
    ) -> OperationIntegrityResult:
        integrity_request = IntegrityRequest(
            operation_id=request.operation_id,
            operation_type=request.operation_type,
            source=request.source,
            actor=request.user_id,
            origin="FINANCIAL_CORE",
            target=request.target,
            payload={
                "amount": request.amount,
                "unit": request.unit,
                **dict(request.metadata),
            },
            value=request.amount,
            previous_hash=previous_hash,
        )

        result = self._integrity.generate(integrity_request)

        return OperationIntegrityResult(
            operation_id=request.operation_id,
            operation_type=request.operation_type,
            integrity_version=result.integrity_version,
            algorithm=result.algorithm,
            hash_value=result.hash_value,
            previous_hash=result.previous_hash,
            authority="UNIVERSAL_INTEGRITY_LAYER",
            metadata={
                **dict(result.metadata),
                "financial_operation": True,
                "source_boundary": "FINANCIAL_CORE",
            },
        )
