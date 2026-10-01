"""Financial operation execution with integrity reference."""

from dataclasses import dataclass, field
from typing import Any, Mapping


@dataclass(frozen=True)
class OperationExecutionIntegrityResult:
    """
    Execution result linked to the integrity record of the operation.

    This contract does not define a ledger or blockchain state.
    """

    operation_id: str
    operation_type: str
    status: str
    integrity_hash: str
    integrity_version: str
    integrity_algorithm: str
    integrity_authority: str
    metadata: Mapping[str, Any] = field(default_factory=dict)
