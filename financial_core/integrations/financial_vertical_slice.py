"""End-to-end financial vertical slice: transfer, accounting, integrity."""

from decimal import Decimal
from pathlib import Path

from financial_core.accounting.sqlite_store import SQLiteAccountingEntryStore
from financial_core.accounting.transfer_accounting import TransferAccountingRecorder
from financial_core.contracts.integrity import IntegrityRequest
from financial_core.contracts.integrity_verification import (
    IntegrityVerificationRequest,
)
from financial_core.contracts.transfer import TransferRequest
from financial_core.idempotency.memory_store import InMemoryIdempotencyStore
from financial_core.integrations.integrity_adapter import UniversalIntegrityAdapter
from financial_core.integrations.integrity_verifier import UniversalIntegrityVerifier
from financial_core.operations.transfer_executor import TransferExecutor
from platform_core.universal_value.ledger.value_ledger import ValueLedger


class FinancialTransferVerticalSlice:
    """Executes and verifies one complete financial transfer flow."""

    def __init__(self, database_path: str | Path):
        self._ledger = ValueLedger()
        self._accounting = SQLiteAccountingEntryStore(database_path)
        self._integrity = UniversalIntegrityAdapter()
        self._verifier = UniversalIntegrityVerifier()

    def execute(self, request: TransferRequest) -> dict:
        self._ledger.record(
            transaction_id=f"{request.operation_id}:seed",
            event_id=f"{request.operation_id}:seed-event",
            user_id=request.source_account_id,
            amount=Decimal("100"),
            currency=request.unit,
            transaction_type="CREDIT",
        )

        source_before = self._ledger.balance(
            request.source_account_id,
            request.unit,
        )
        destination_before = self._ledger.balance(
            request.destination_account_id,
            request.unit,
        )

        executor = TransferExecutor(
            ledger=self._ledger,
            idempotency_store=InMemoryIdempotencyStore(),
        )

        execution = executor.execute(request)

        source_after_transfer = self._ledger.balance(
            request.source_account_id,
            request.unit,
        )
        destination_after_transfer = self._ledger.balance(
            request.destination_account_id,
            request.unit,
        )

        recorder = TransferAccountingRecorder()
        debit, credit = recorder.create_entries(execution)

        self._accounting.save(debit)
        self._accounting.save(credit)

        integrity = self._integrity.generate(
            IntegrityRequest(
                operation_id=request.operation_id,
                operation_type="TRANSFER_ACCOUNTING",
                source="FINANCIAL_CORE",
                actor=request.source_account_id,
                origin="ACCOUNTING",
                target=request.destination_account_id,
                payload={
                    "debit_entry_id": debit.entry_id,
                    "credit_entry_id": credit.entry_id,
                    "debit_account_id": debit.account_id,
                    "credit_account_id": credit.account_id,
                    "amount": request.amount,
                    "unit": request.unit,
                    "debit_direction": debit.direction,
                    "credit_direction": credit.direction,
                },
                value=request.amount,
                previous_hash="GENESIS",
            )
        )

        verification = self._verifier.verify(
            IntegrityVerificationRequest(
                operation_id=request.operation_id,
                operation_type="TRANSFER_ACCOUNTING",
                source="FINANCIAL_CORE",
                actor=request.source_account_id,
                origin="ACCOUNTING",
                target=request.destination_account_id,
                payload={
                    "debit_entry_id": debit.entry_id,
                    "credit_entry_id": credit.entry_id,
                    "debit_account_id": debit.account_id,
                    "credit_account_id": credit.account_id,
                    "amount": request.amount,
                    "unit": request.unit,
                    "debit_direction": debit.direction,
                    "credit_direction": credit.direction,
                },
                value=request.amount,
                previous_hash="GENESIS",
                hash_value=integrity.hash_value,
            )
        )

        tampered = self._verifier.verify(
            IntegrityVerificationRequest(
                operation_id=request.operation_id,
                operation_type="TRANSFER_ACCOUNTING",
                source="FINANCIAL_CORE",
                actor=request.source_account_id,
                origin="ACCOUNTING",
                target=request.destination_account_id,
                payload={
                    "debit_entry_id": debit.entry_id,
                    "credit_entry_id": credit.entry_id,
                    "debit_account_id": debit.account_id,
                    "credit_account_id": credit.account_id,
                    "amount": "50",
                    "unit": request.unit,
                    "debit_direction": debit.direction,
                    "credit_direction": credit.direction,
                },
                value="50",
                previous_hash="GENESIS",
                hash_value=integrity.hash_value,
            )
        )

        source_after_accounting = self._ledger.balance(
            request.source_account_id,
            request.unit,
        )
        destination_after_accounting = self._ledger.balance(
            request.destination_account_id,
            request.unit,
        )

        return {
            "operation_id": request.operation_id,
            "transfer_status": execution.status,
            "source_before": source_before,
            "destination_before": destination_before,
            "source_after_transfer": source_after_transfer,
            "destination_after_transfer": destination_after_transfer,
            "source_after_accounting": source_after_accounting,
            "destination_after_accounting": destination_after_accounting,
            "debit_entry": self._accounting.get(debit.entry_id),
            "credit_entry": self._accounting.get(credit.entry_id),
            "integrity_hash": integrity.hash_value,
            "integrity_version": integrity.integrity_version,
            "integrity_verified": verification.valid,
            "integrity_reason": verification.reason,
            "tampered_verified": tampered.valid,
            "tampered_reason": tampered.reason,
        }
