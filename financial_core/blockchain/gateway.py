"""Blockchain settlement gateway implementation."""

from financial_core.settlement.contracts import (
    SettlementRecord,
    SettlementRequest,
)
from financial_core.settlement.gateway import BlockchainGateway


class BlockchainSettlementGateway(BlockchainGateway):
    """
    Concrete blockchain settlement boundary.

    This implementation does not perform network I/O yet.
    It creates a deterministic settlement record that can later
    be backed by a real blockchain adapter.
    """

    def settle(
        self,
        request: SettlementRequest,
    ) -> SettlementRecord:
        return SettlementRecord(
            operation_id=request.operation_id,
            settlement_type=request.settlement_type,
            amount=request.amount,
            unit=request.unit,
            status="SUBMITTED",
            metadata={
                **dict(request.metadata),
                "settlement_mode": "ON_CHAIN",
                "blockchain_status": "PENDING_SUBMISSION",
            },
        )
