"""Accounting records generated from executed transfers."""

from financial_core.contracts.accounting import AccountingEntry
from financial_core.contracts.transfer_execution import TransferExecutionResult


class TransferAccountingRecorder:
    """
    Creates accounting entries from a successful transfer.

    Accounting does not own or mutate financial balances.
    """

    def create_entries(
        self,
        result: TransferExecutionResult,
    ) -> tuple[AccountingEntry, AccountingEntry]:

        if result.status != "EXECUTED":
            raise ValueError(
                "accounting entries require an executed transfer"
            )

        debit = AccountingEntry(
            entry_id=f"{result.transfer_id}:DEBIT",
            operation_id=result.operation_id,
            account_id=result.source_account_id,
            entry_type="TRANSFER",
            amount=result.amount,
            unit=result.unit,
            direction="DEBIT",
            description="Transfer source accounting entry",
        )

        credit = AccountingEntry(
            entry_id=f"{result.transfer_id}:CREDIT",
            operation_id=result.operation_id,
            account_id=result.destination_account_id,
            entry_type="TRANSFER",
            amount=result.amount,
            unit=result.unit,
            direction="CREDIT",
            description="Transfer destination accounting entry",
        )

        return debit, credit
