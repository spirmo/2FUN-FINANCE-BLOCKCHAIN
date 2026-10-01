"""UVI integration contract.

This contract defines the Financial Core boundary to the existing
Universal Value Infrastructure (UVI).

The Financial Core does not own value calculation or UVI ledger state.
"""

from dataclasses import dataclass
from typing import Any, Mapping, Protocol


@dataclass(frozen=True)
class UVIValueRequest:
    """Value request forwarded to the existing UVI."""

    operation_id: str
    user_id: str
    amount: str
    unit: str
    metadata: Mapping[str, Any]


@dataclass(frozen=True)
class UVIValueResult:
    """Value result returned by the existing UVI."""

    operation_id: str
    status: str
    recorded: bool
    metadata: Mapping[str, Any]


class UVIAdapter(Protocol):
    """Boundary contract for the existing UVI."""

    def process(
        self,
        request: UVIValueRequest,
    ) -> UVIValueResult:
        """Process a value operation through the existing UVI."""
        ...
