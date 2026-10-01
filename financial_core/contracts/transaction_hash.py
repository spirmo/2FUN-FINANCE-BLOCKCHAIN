"""Transaction hash ownership contract.

Financial Core owns the financial transaction hash.
The existing UVI owns the UVI transaction identifier.
Blockchain owns the on-chain transaction hash.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class TransactionIdentity:
    """Immutable identity references for a financial transaction."""

    operation_id: str
    uvi_transaction_id: str
    financial_transaction_hash: str | None = None
    blockchain_tx_hash: str | None = None


class TransactionHashAuthority:
    """Define ownership boundaries for transaction identifiers and hashes."""

    UVI_ID_OWNER = "EXISTING_UVI"
    FINANCIAL_HASH_OWNER = "FINANCIAL_CORE"
    BLOCKCHAIN_HASH_OWNER = "BLOCKCHAIN"

    @classmethod
    def describe(cls) -> dict[str, str]:
        """Return the authoritative ownership map."""

        return {
            "uvi_transaction_id": cls.UVI_ID_OWNER,
            "financial_transaction_hash": cls.FINANCIAL_HASH_OWNER,
            "blockchain_tx_hash": cls.BLOCKCHAIN_HASH_OWNER,
        }
