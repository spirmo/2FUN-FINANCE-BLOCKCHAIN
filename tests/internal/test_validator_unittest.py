"""EX-011 Internal transfer validator tests."""

import unittest

from financial_core.internal.contracts import InternalTransferRequest
from financial_core.internal.validator import InternalTransferValidator


class TestInternalTransferValidator(unittest.TestCase):

    def setUp(self):
        self.validator = InternalTransferValidator()

    def test_valid_transfer_is_approved(self):
        request = InternalTransferRequest(
            operation_id="INT-001",
            source_user_id="USER-001",
            target_user_id="USER-002",
            amount="100",
            unit="POINT",
        )

        decision = self.validator.validate(request)

        self.assertTrue(decision.approved)
        self.assertIsNone(decision.reason)

    def test_same_user_is_rejected(self):
        request = InternalTransferRequest(
            operation_id="INT-002",
            source_user_id="USER-001",
            target_user_id="USER-001",
            amount="100",
            unit="POINT",
        )

        decision = self.validator.validate(request)

        self.assertFalse(decision.approved)
        self.assertEqual(
            decision.reason,
            "source and target users must differ",
        )

    def test_zero_amount_is_rejected(self):
        request = InternalTransferRequest(
            operation_id="INT-003",
            source_user_id="USER-001",
            target_user_id="USER-002",
            amount="0",
            unit="POINT",
        )

        decision = self.validator.validate(request)

        self.assertFalse(decision.approved)
        self.assertEqual(
            decision.reason,
            "amount must be greater than zero",
        )

    def test_invalid_amount_is_rejected(self):
        request = InternalTransferRequest(
            operation_id="INT-004",
            source_user_id="USER-001",
            target_user_id="USER-002",
            amount="invalid",
            unit="POINT",
        )

        decision = self.validator.validate(request)

        self.assertFalse(decision.approved)
        self.assertEqual(
            decision.reason,
            "amount must be a valid decimal",
        )


if __name__ == "__main__":
    unittest.main()
