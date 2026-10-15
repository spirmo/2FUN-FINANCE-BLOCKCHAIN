"""Blockchain network adapter contracts."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class BlockchainSubmissionRequest:
    """Request submitted from Financial Core to the blockchain boundary."""

    operation_id: str
    amount: str
    unit: str
    metadata: Mapping[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class BlockchainSubmissionResult:
    """Result returned by the blockchain boundary."""

    operation_id: str
    status: str
    blockchain_tx_hash: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
