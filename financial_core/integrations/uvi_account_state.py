"""UVI-backed financial account state reader."""

from platform_core.universal_value.ledger.value_ledger import ValueLedger

from financial_core.contracts.account import FinancialAccount
from financial_core.contracts.financial_account_state import (
    FinancialAccountState,
    FinancialAccountStateRequest,
)


class UVIAccountStateReader:
    """
    Reads financial value state from the existing UVI ledger.

    Financial Core owns account identity/status.
    UVI remains authoritative for value balance.
    """

    def __init__(
        self,
        ledger: ValueLedger,
    ):
        self._ledger = ledger

    def read(
        self,
        account: FinancialAccount,
        request: FinancialAccountStateRequest,
    ) -> FinancialAccountState:
        if request.account_id != account.account_id:
            raise ValueError(
                "account_id does not match financial account"
            )

        balance = self._ledger.balance(
            account.account_id,
            request.unit,
        )

        return FinancialAccountState(
            account_id=account.account_id,
            owner_id=account.owner_id,
            account_type=account.account_type,
            status=account.status,
            unit=request.unit,
            balance=str(balance),
            value_authority="EXISTING_UVI",
        )
