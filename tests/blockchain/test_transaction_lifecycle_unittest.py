import unittest

from financial_core.blockchain.transaction_lifecycle import (
    TransactionLifecycle,
    TransactionStatus,
)


class TransactionLifecycleTests(unittest.TestCase):
    def test_created_to_pending_to_submitted(self):
        tx = TransactionLifecycle("op-001")

        tx = tx.transition(TransactionStatus.PENDING_SUBMISSION)
        self.assertEqual(tx.status, TransactionStatus.PENDING_SUBMISSION)

        tx = tx.transition(
            TransactionStatus.SUBMITTED,
            transaction_hash="0xabc",
        )
        self.assertEqual(tx.status, TransactionStatus.SUBMITTED)
        self.assertEqual(tx.transaction_hash, "0xabc")

    def test_cannot_finalize_without_network_evidence(self):
        tx = TransactionLifecycle(
            "op-002",
            status=TransactionStatus.CONFIRMED,
            transaction_hash="0xdef",
            confirmations=3,
        )

        with self.assertRaisesRegex(ValueError, "validated network evidence"):
            tx.transition(
                TransactionStatus.FINALIZED,
                finality_reached=True,
            )

    def test_cannot_finalize_before_finality(self):
        tx = TransactionLifecycle(
            "op-003",
            status=TransactionStatus.CONFIRMED,
            transaction_hash="0x123",
            confirmations=3,
        )

        with self.assertRaisesRegex(ValueError, "finality condition"):
            tx.transition(
                TransactionStatus.FINALIZED,
                valid_network_confirmation=True,
                finality_reached=False,
            )

    def test_finalization_requires_hash(self):
        tx = TransactionLifecycle(
            "op-004",
            status=TransactionStatus.CONFIRMED,
            transaction_hash=None,
            confirmations=2,
        )

        with self.assertRaisesRegex(ValueError, "requires a transaction hash"):
            tx.transition(
                TransactionStatus.FINALIZED,
                valid_network_confirmation=True,
                finality_reached=True,
            )

    def test_cannot_leave_finalized_state(self):
        tx = TransactionLifecycle(
            "op-005",
            status=TransactionStatus.FINALIZED,
            transaction_hash="0x456",
            confirmations=5,
        )

        with self.assertRaisesRegex(ValueError, "invalid transaction transition"):
            tx.transition(TransactionStatus.REORGED)

    def test_confirming_requires_confirmation_count(self):
        tx = TransactionLifecycle(
            "op-006",
            status=TransactionStatus.SUBMITTED,
            transaction_hash="0x789",
        )

        with self.assertRaisesRegex(ValueError, "at least one confirmation"):
            tx.transition(
                TransactionStatus.CONFIRMING,
                valid_network_confirmation=True,
                confirmations=0,
            )

    def test_reorg_can_return_to_pending_submission(self):
        tx = TransactionLifecycle(
            "op-007",
            status=TransactionStatus.REORGED,
            transaction_hash="0xaaa",
        )

        updated = tx.transition(TransactionStatus.PENDING_SUBMISSION)
        self.assertEqual(
            updated.status,
            TransactionStatus.PENDING_SUBMISSION,
        )

    def test_negative_confirmations_are_rejected(self):
        tx = TransactionLifecycle("op-008")

        with self.assertRaisesRegex(ValueError, "cannot be negative"):
            tx.transition(
                TransactionStatus.PENDING_SUBMISSION,
                confirmations=-1,
            )


if __name__ == "__main__":
    unittest.main()
