"""Universal integrity verification contracts."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class IntegrityVerificationRequest:
    """
    Request to verify an integrity hash through the central
    Universal Integrity Layer.
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
    hash_value: str = ""


@dataclass(frozen=True)
class IntegrityVerificationResult:
    """
    Result of universal integrity verification.
    """

    operation_id: str
    valid: bool
    reason: str
    integrity_version: str
    algorithm: str
    hash_value: str
    previous_hash: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


class IntegrityVerifier:
    """
    Boundary protocol for integrity verification.

    The concrete hash implementation remains outside Financial Core.
    """

    def verify(
        self,
        request: IntegrityVerificationRequest,
    ) -> IntegrityVerificationResult:
        """
        Verify an integrity record.
        """
        raise NotImplementedError
