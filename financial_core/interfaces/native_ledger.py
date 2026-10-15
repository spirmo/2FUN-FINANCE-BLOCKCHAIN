"""Native ledger contract shared across Financial Core subsystems."""

from dataclasses import dataclass
from typing import Protocol


class LedgerError(ValueError):
    """Base exception for native-ledger contract failures."""


class DuplicateTransaction(LedgerError):
    """A transaction identifier has already been used."""


@dataclass(frozen=True)
class Issuance:
    """Auditable record of a successful native 2FUNC issuance."""

    tx_id: str
    recipient: str
    amount: int


class NativeLedgerPort(Protocol):
    """Minimum ledger operations required by the 2FUNC issuance coordinator."""

    def issue_to(self, tx_id: str, recipient: str, amount: int) -> Issuance:
        """Issue an exact integer amount of native base units."""
        ...

    def issuance_for(self, tx_id: str) -> Issuance | None:
        """Return the issuance record for a transaction, if present."""
        ...

    def transaction_exists(self, tx_id: str) -> bool:
        """Return whether the transaction identifier is already in use."""
        ...
