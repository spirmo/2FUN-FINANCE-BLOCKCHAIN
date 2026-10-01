"""Blockchain Gateway boundary for settlement."""

from abc import ABC, abstractmethod

from financial_core.settlement.contracts import (
    SettlementRequest,
    SettlementRecord,
)


class BlockchainGateway(ABC):
    """
    Controlled boundary between Financial Core and Blockchain.

    Settlement depends only on this interface and does not know
    blockchain-specific implementation details.
    """

    @abstractmethod
    def settle(self, request: SettlementRequest) -> SettlementRecord:
        """Submit an approved settlement to the blockchain boundary."""
        raise NotImplementedError
