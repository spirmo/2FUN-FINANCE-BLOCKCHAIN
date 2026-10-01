"""Valuation contract for value-aware financial calculations.

Financial Core does not own market valuation.
It consumes a verified valuation result from an external
valuation authority / oracle boundary.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class ValuationRequest:
    """Request for a valuation at a specific point in time."""

    asset: str
    quote_asset: str
    timestamp: str
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class ValuationResult:
    """Verified valuation returned by the valuation boundary."""

    asset: str
    quote_asset: str
    price: str
    timestamp: str
    source: str
    verified: bool
    metadata: Mapping[str, Any]


class ValuationProvider(Protocol):
    """Boundary contract for an external valuation authority."""

    def get_value(
        self,
        request: ValuationRequest,
    ) -> ValuationResult:
        """Return a verified valuation for the requested asset."""
        ...
