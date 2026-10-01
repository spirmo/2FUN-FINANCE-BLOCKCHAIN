"""Idempotency domain contracts."""

from dataclasses import dataclass


@dataclass(frozen=True)
class IdempotencyDecision:
    """Decision for an operation id."""

    operation_id: str
    accepted: bool
    reason: str | None = None
