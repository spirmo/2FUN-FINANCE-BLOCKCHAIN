"""In-memory implementation of the financial account state store."""

from financial_core.contracts.account import FinancialAccount


class InMemoryAccountStateStore:
    """Temporary account state store for execution and testing."""

    def __init__(self):
        self._accounts: dict[str, FinancialAccount] = {}

    def get_account(
        self,
        account_id: str,
    ) -> FinancialAccount | None:
        """Return an account or None when it does not exist."""

        return self._accounts.get(account_id)

    def save_account(
        self,
        account: FinancialAccount,
    ) -> None:
        """Persist an account in memory."""

        if not account.account_id:
            raise ValueError("account_id is required")

        self._accounts[account.account_id] = account
