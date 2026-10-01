from financial_core.contracts.operation_execution_integrity import (
    OperationExecutionIntegrityResult,
)
from financial_core.contracts.operation_integrity import (
    OperationIntegrityResult,
)


class OperationExecutionIntegrityAdapter:
    """
    Links a financial execution result to its integrity record.

    This adapter does not execute operations and does not mutate
    UVI, account, settlement, or blockchain state.
    """

    def build_result(
        self,
        integrity_result: OperationIntegrityResult,
        status: str,
        metadata: dict | None = None,
    ) -> OperationExecutionIntegrityResult:
        if not integrity_result.hash_value:
            raise ValueError("integrity hash is required")

        return OperationExecutionIntegrityResult(
            operation_id=integrity_result.operation_id,
            operation_type=integrity_result.operation_type,
            status=status,
            integrity_hash=integrity_result.hash_value,
            integrity_version=integrity_result.integrity_version,
            integrity_algorithm=integrity_result.algorithm,
            integrity_authority="UNIVERSAL_INTEGRITY_LAYER",
            metadata={
                **dict(integrity_result.metadata),
                **(metadata or {}),
            },
        )
