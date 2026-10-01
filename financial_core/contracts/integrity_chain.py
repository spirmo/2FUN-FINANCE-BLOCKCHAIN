"""Universal integrity chain verification contracts."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class IntegrityChainVerificationRequest:
    """
    Request to verify a sequence of integrity records.
    """

    records: tuple[Mapping[str, Any], ...]
    previous_hash: str = "GENESIS"


@dataclass(frozen=True)
class IntegrityChainVerificationResult:
    """
    Result of universal integrity chain verification.
    """

    valid: bool
    reason: str
    total: int
    failed_index: int | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)


class IntegrityChainVerifier:
    """
    Boundary protocol for universal integrity chain verification.
    """

    def verify(
        self,
        request: IntegrityChainVerificationRequest,
    ) -> IntegrityChainVerificationResult:
        """
        Verify an integrity chain.
        """
        raise NotImplementedError
