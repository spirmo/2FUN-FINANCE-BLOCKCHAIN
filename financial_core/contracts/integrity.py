"""Universal integrity boundary contracts."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class IntegrityRequest:
    """
    Request from Financial Core to the central Universal Integrity Layer.

    Financial Core owns the request semantics.
    The Universal Integrity Layer owns hash generation.
    """

    operation_id: str
    operation_type: str
    source: str
    actor: str | None = None
    origin: str | None = None
    target: str | None = None
    payload: Mapping[str, Any] = field(default_factory=dict)
    value: Any = None
    previous_hash: str = "GENESIS"


@dataclass(frozen=True)
class IntegrityResult:
    """
    Result returned by the Universal Integrity Layer.
    """

    operation_id: str
    integrity_version: str
    hash_value: str
    previous_hash: str
    algorithm: str
    verified: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)


class IntegrityProvider:
    """
    Boundary protocol for the central Universal Integrity Layer.

    Financial Core must depend on this boundary rather than on a
    concrete hash implementation.
    """

    def generate(
        self,
        request: IntegrityRequest,
    ) -> IntegrityResult:
        """
        Generate integrity information for a financial operation.
        """
        raise NotImplementedError
