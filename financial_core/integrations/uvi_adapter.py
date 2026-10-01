"""Adapter between Financial Core and the existing UVI."""

from financial_core.contracts.uvi import (
    UVIAdapter,
    UVIValueRequest,
    UVIValueResult,
)


class ExistingUVIAdapter(UVIAdapter):
    """Financial Core adapter for the existing 2FUN-OS UVI."""

    def process(
        self,
        request: UVIValueRequest,
    ) -> UVIValueResult:
        """Validate the boundary without mutating UVI state."""

        return UVIValueResult(
            operation_id=request.operation_id,
            status="READY_FOR_UVI_EXECUTION",
            recorded=False,
            metadata={
                "authority": "EXISTING_UVI",
                "unit": request.unit,
                "execution": "NOT_EXECUTED",
            },
        )
