"""Integrity-verified idempotent transfer contract."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class IntegrityIdempotentTransferResult:
    operation_id: str
    status: str
    integrity_verified: bool
    duplicate: bool
    transfer_id: str | None = None
    integrity_hash: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)
