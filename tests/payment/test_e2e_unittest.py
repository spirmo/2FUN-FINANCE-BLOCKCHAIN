import tempfile
import unittest
from pathlib import Path

from financial_core.contracts.payment import PaymentRequest
from financial_core.idempotency.sqlite_store import SQLiteIdempotencyStore
from financial_core.operations.payment_executor import PaymentExecutor
from financial_core.operations.transfer_executor import TransferExecutor
from platform_core.universal_value.core.contracts import ValueEvent
from platform_core.universal_value.ledger.value_ledger import ValueLedger
from platform_core.universal_value.transactions.transaction_manager import (
    TransactionManager,
)


class TestPaymentE2E(unittest.TestCase):
    def test_payment_persists_idempotency_and_blocks_second_mutation(self):
        ledger = ValueLedger()
        transaction_manager = TransactionManager(ledger)

        transaction_manager.create_transaction(
            event=ValueEvent(
                event_id="VS004-E2E-INITIAL-CREDIT",
                user_id="PAYER-VS004",
                source="VS004",
                action="CREDIT",
                base_value=100,
                currency="POINT",
                metadata={"test": "VS004"},
            ),
            amount=100,
            transaction_type="CREDIT",
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            database_path = Path(temp_dir) / "idempotency.sqlite3"
            store = SQLiteIdempotencyStore(database_path)

            transfer_executor = TransferExecutor(
                ledger,
                idempotency_store=store,
            )
            payment_executor = PaymentExecutor(
                ledger,
                transfer_executor=transfer_executor,
            )

            request = PaymentRequest(
                operation_id="VS004-E2E-PAYMENT-001",
                payer_account_id="PAYER-VS004",
                payee_account_id="PAYEE-VS004",
                amount="25",
                unit="POINT",
                metadata={"test": "VS004"},
            )

            first = payment_executor.execute(request)

            self.assertEqual(first.status, "EXECUTED")
            self.assertEqual(first.payment_id, request.operation_id)
            self.assertEqual(first.transfer_operation_id, request.operation_id)
            self.assertEqual(
                ledger.balance("PAYER-VS004", "POINT"),
                75,
            )
            self.assertEqual(
                ledger.balance("PAYEE-VS004", "POINT"),
                25,
            )
            self.assertIsNotNone(first.payer_uvi_transaction_id)
            self.assertIsNotNone(first.payee_uvi_transaction_id)
            self.assertIsNotNone(first.financial_transaction_hash)

            first_payer_balance = ledger.balance("PAYER-VS004", "POINT")
            first_payee_balance = ledger.balance("PAYEE-VS004", "POINT")

            second = payment_executor.execute(request)

            self.assertEqual(second.status, "EXECUTED")
            self.assertEqual(second.payment_id, first.payment_id)
            self.assertEqual(
                second.transfer_operation_id,
                first.transfer_operation_id,
            )
            self.assertEqual(
                second.payer_uvi_transaction_id,
                first.payer_uvi_transaction_id,
            )
            self.assertEqual(
                second.payee_uvi_transaction_id,
                first.payee_uvi_transaction_id,
            )
            self.assertEqual(
                second.financial_transaction_hash,
                first.financial_transaction_hash,
            )

            self.assertEqual(
                ledger.balance("PAYER-VS004", "POINT"),
                first_payer_balance,
            )
            self.assertEqual(
                ledger.balance("PAYEE-VS004", "POINT"),
                first_payee_balance,
            )

            persisted = store.get(request.operation_id)

            self.assertIsNotNone(persisted)
            self.assertEqual(
                persisted.operation_id,
                request.operation_id,
            )
            self.assertEqual(
                persisted.financial_transaction_hash,
                first.financial_transaction_hash,
            )


if __name__ == "__main__":
    unittest.main()
