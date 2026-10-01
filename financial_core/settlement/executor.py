"""Settlement execution."""

from financial_core.settlement.contracts import (
    SettlementRecord,
    SettlementRequest,
)
from financial_core.settlement.gateway import BlockchainGateway
from financial_core.settlement.validator import SettlementValidator


class SettlementExecutor:
    """
    Execute settlement decisions.

    Internal settlement is finalized inside the Financial Core.
    On-chain settlement is delegated exclusively to BlockchainGateway.
    """

    def __init__(
        self,
        blockchain_gateway: BlockchainGateway | None = None,
    ):
        self._validator = SettlementValidator()
        self._blockchain_gateway = blockchain_gateway

    def execute(
        self,
        request: SettlementRequest,
    ) -> SettlementRecord:
        decision = self._validator.validate(request)

        if not decision.approved:
            raise ValueError(decision.reason)

        if request.settlement_type == "INTERNAL":
            return SettlementRecord(
                operation_id=request.operation_id,
                settlement_type=request.settlement_type,
                amount=request.amount,
                unit=request.unit,
                status="SETTLED",
                metadata={
                    **dict(request.metadata),
                    "settlement_mode": "INTERNAL",
                },
            )

        if self._blockchain_gateway is None:
            raise RuntimeError(
                "BlockchainGateway is required for ON_CHAIN settlement"
            )

        return self._blockchain_gateway.settle(request)
