"""Explicit lifecycle rules for 2FUNC blockchain transactions."""

from dataclasses import dataclass
from enum import Enum


class TransactionStatus(str, Enum):
    CREATED = "CREATED"
    PENDING_SUBMISSION = "PENDING_SUBMISSION"
    SUBMITTED = "SUBMITTED"
    CONFIRMING = "CONFIRMING"
    CONFIRMED = "CONFIRMED"
    FINALIZED = "FINALIZED"
    FAILED = "FAILED"
    REORGED = "REORGED"


_ALLOWED_TRANSITIONS = {
    TransactionStatus.CREATED: {
        TransactionStatus.PENDING_SUBMISSION,
        TransactionStatus.FAILED,
    },
    TransactionStatus.PENDING_SUBMISSION: {
        TransactionStatus.SUBMITTED,
        TransactionStatus.FAILED,
    },
    TransactionStatus.SUBMITTED: {
        TransactionStatus.CONFIRMING,
        TransactionStatus.CONFIRMED,
        TransactionStatus.FAILED,
        TransactionStatus.REORGED,
    },
    TransactionStatus.CONFIRMING: {
        TransactionStatus.CONFIRMED,
        TransactionStatus.FAILED,
        TransactionStatus.REORGED,
    },
    TransactionStatus.CONFIRMED: {
        TransactionStatus.FINALIZED,
        TransactionStatus.REORGED,
    },
    TransactionStatus.REORGED: {
        TransactionStatus.PENDING_SUBMISSION,
        TransactionStatus.FAILED,
    },
    TransactionStatus.FINALIZED: set(),
    TransactionStatus.FAILED: set(),
}


@dataclass(frozen=True)
class TransactionLifecycle:
    operation_id: str
    status: TransactionStatus = TransactionStatus.CREATED
    transaction_hash: str | None = None
    confirmations: int = 0

    def transition(
        self,
        new_status: TransactionStatus,
        *,
        transaction_hash: str | None = None,
        confirmations: int | None = None,
        valid_network_confirmation: bool = False,
        finality_reached: bool = False,
    ) -> "TransactionLifecycle":
        if not self.operation_id.strip():
            raise ValueError("operation_id must not be empty")

        if not isinstance(new_status, TransactionStatus):
            raise TypeError("new_status must be a TransactionStatus")

        if new_status not in _ALLOWED_TRANSITIONS[self.status]:
            raise ValueError(
                f"invalid transaction transition: "
                f"{self.status.value} -> {new_status.value}"
            )

        next_hash = (
            transaction_hash
            if transaction_hash is not None
            else self.transaction_hash
        )
        next_confirmations = (
            confirmations
            if confirmations is not None
            else self.confirmations
        )

        if next_confirmations < 0:
            raise ValueError("confirmations cannot be negative")

        if new_status in {
            TransactionStatus.SUBMITTED,
            TransactionStatus.CONFIRMING,
            TransactionStatus.CONFIRMED,
            TransactionStatus.FINALIZED,
        } and not next_hash:
            raise ValueError(
                f"{new_status.value} requires a transaction hash"
            )

        if new_status in {
            TransactionStatus.CONFIRMING,
            TransactionStatus.CONFIRMED,
            TransactionStatus.FINALIZED,
        } and not valid_network_confirmation:
            raise ValueError(
                f"{new_status.value} requires validated network evidence"
            )

        if new_status == TransactionStatus.FINALIZED:
            if not finality_reached:
                raise ValueError(
                    "FINALIZED requires the network finality condition"
                )
            if self.status != TransactionStatus.CONFIRMED:
                raise ValueError(
                    "only a CONFIRMED transaction can be finalized"
                )

        if new_status == TransactionStatus.CONFIRMING:
            if next_confirmations < 1:
                raise ValueError(
                    "CONFIRMING requires at least one confirmation"
                )

        return TransactionLifecycle(
            operation_id=self.operation_id,
            status=new_status,
            transaction_hash=next_hash,
            confirmations=next_confirmations,
        )
