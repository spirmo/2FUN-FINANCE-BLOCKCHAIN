"""Blockchain settlement gateway implementation."""

import hashlib

from financial_core.contracts.transaction_hash import TransactionIdentity
from financial_core.settlement.contracts import (
    SettlementRecord,
    SettlementRequest,
)
from financial_core.settlement.gateway import BlockchainGateway


class BlockchainSettlementGateway(BlockchainGateway):
    """
    Concrete blockchain settlement boundary.

    This adapter does not perform network I/O yet.
    It creates a deterministic blockchain submission reference
    while preserving transaction-hash ownership boundaries.
    """

    def settle(
        self,
        request: SettlementRequest,
    ) -> SettlementRecord:
        payload = (
            f"{request.operation_id}|"
            f"{request.settlement_type}|"
            f"{request.amount}|"
            f"{request.unit}"
        )

        submission_reference = (
            "bc-submit-"
            + hashlib.sha256(payload.encode("utf-8")).hexdigest()
        )

        identity = TransactionIdentity(
            operation_id=request.operation_id,
            uvi_transaction_id=str(
                request.metadata.get("uvi_transaction_id", "")
            ),
            financial_transaction_hash=request.metadata.get(
                "financial_transaction_hash"
            ),
            blockchain_tx_hash=submission_reference,
        )

        metadata = {
            **dict(request.metadata),
            "settlement_mode": "ON_CHAIN",
            "blockchain_status": "PENDING_SUBMISSION",
            "transaction_identity": identity,
            "blockchain_tx_hash": identity.blockchain_tx_hash,
        }

        return SettlementRecord(
            operation_id=request.operation_id,
            settlement_type=request.settlement_type,
            amount=request.amount,
            unit=request.unit,
            status="SUBMITTED",
            transaction_reference=submission_reference,
            metadata=metadata,
        )
