"""Blockchain network adapter boundary."""

from abc import ABC, abstractmethod

from financial_core.blockchain.contracts import (
    BlockchainSubmissionRequest,
    BlockchainSubmissionResult,
)


class BlockchainNetworkAdapter(ABC):
    """
    Boundary for submitting approved transactions to a blockchain network.

    The adapter owns blockchain-specific network behavior.
    Financial Core does not generate or own blockchain transaction hashes.
    """

    @abstractmethod
    def submit(
        self,
        request: BlockchainSubmissionRequest,
    ) -> BlockchainSubmissionResult:
        """Submit a transaction to the blockchain network."""
        raise NotImplementedError
