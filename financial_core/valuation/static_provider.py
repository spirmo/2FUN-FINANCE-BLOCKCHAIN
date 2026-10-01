"""Deterministic valuation provider for integration testing."""

from financial_core.contracts.valuation import (
    ValuationRequest,
    ValuationResult,
)


class StaticValuationProvider:
    """Test-only provider implementing the valuation boundary."""

    def __init__(self, price: str):
        self._price = price

    def get_value(
        self,
        request: ValuationRequest,
    ) -> ValuationResult:
        return ValuationResult(
            asset=request.asset,
            quote_asset=request.quote_asset,
            price=self._price,
            timestamp=request.timestamp,
            source="STATIC_TEST_PROVIDER",
            verified=True,
            metadata=dict(request.metadata),
        )
