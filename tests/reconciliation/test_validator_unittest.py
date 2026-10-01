import unittest

from financial_core.reconciliation.contracts import ReconciliationRequest
from financial_core.reconciliation.validator import ReconciliationValidator


class TestReconciliationValidator(unittest.TestCase):

    def setUp(self):
        self.validator = ReconciliationValidator()

    def test_matching_amounts(self):
        request = ReconciliationRequest(
            operation_id="EX016-001",
            expected_amount="100",
            recorded_amount="100",
            unit="POINT",
        )

        decision = self.validator.validate(request)

        self.assertEqual(decision.status, "MATCHED")
        self.assertEqual(decision.difference, "0")
        self.assertIsNone(decision.reason)

    def test_mismatch_is_detected(self):
        request = ReconciliationRequest(
            operation_id="EX016-002",
            expected_amount="100",
            recorded_amount="90",
            unit="POINT",
        )

        decision = self.validator.validate(request)

        self.assertEqual(decision.status, "MISMATCH")
        self.assertEqual(decision.difference, "-10")
        self.assertEqual(
            decision.reason,
            "expected and recorded amounts differ",
        )

    def test_invalid_amounts_are_rejected(self):
        request = ReconciliationRequest(
            operation_id="EX016-003",
            expected_amount="invalid",
            recorded_amount="100",
            unit="POINT",
        )

        decision = self.validator.validate(request)

        self.assertEqual(decision.status, "REJECTED")

    def test_missing_operation_id_is_rejected(self):
        request = ReconciliationRequest(
            operation_id="",
            expected_amount="100",
            recorded_amount="100",
            unit="POINT",
        )

        decision = self.validator.validate(request)

        self.assertEqual(decision.status, "REJECTED")


if __name__ == "__main__":
    unittest.main()
