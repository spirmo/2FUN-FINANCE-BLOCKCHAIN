"""Financial account state store contract."""

from typing import Protocol

from financial_core.contracts.account import FinancialAccount


class AccountStateStore(Protocol):
    """Authoritative boundary for financial account state."""

    def get_account(self, account_id: str) -> FinancialAccount | None:
        """Return an account or None when it does not exist."""
        ...

    def save_account(self, account: FinancialAccount) -> None:
        """Persist account state."""
        ...
