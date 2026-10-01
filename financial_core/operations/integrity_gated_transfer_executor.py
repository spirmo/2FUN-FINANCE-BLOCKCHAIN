"""Integrity-gated transfer execution."""

from financial_core.contracts.integrity_verification import (
    IntegrityVerificationResult,
)
from financial_core.contracts.transfer import TransferRequest
from financial_core.contracts.transfer_execution import (
    TransferExecutionResult,
)
from financial_core.operations.transfer_executor import TransferExecutor


class IntegrityGatedTransferExecutor:
    """
    Executes a transfer only after successful integrity verification.

    Integrity is a gate; UVI remains the authority for value state.
    """

    def __init__(self, transfer_executor: TransferExecutor):
        self._transfer_executor = transfer_executor

    def execute(
        self,
        request: TransferRequest,
        verification: IntegrityVerificationResult,
    ) -> TransferExecutionResult:
        if verification.operation_id != request.operation_id:
            raise ValueError(
                "integrity verification operation_id does not match transfer"
            )

        if not verification.valid:
            raise ValueError(
                f"integrity verification failed: {verification.reason}"
            )

        return self._transfer_executor.execute(request)
