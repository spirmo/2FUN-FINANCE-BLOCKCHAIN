import unittest

from financial_core.reconciliation.contracts import (
    ReconciliationDecision,
    ReconciliationRequest,
)
from financial_core.reconciliation.executor import ReconciliationExecutor


class TestReconciliationExecutor(unittest.TestCase):

    def test_matching_operation_returns_matched(self):
        executor = ReconciliationExecutor()

        request = ReconciliationRequest(
            operation_id="EX016-EXEC-001",
            expected_amount="250",
            recorded_amount="250",
            unit="SHIR",
        )

        decision = executor.reconcile(request)

        self.assertIsInstance(decision, ReconciliationDecision)
        self.assertEqual(decision.status, "MATCHED")
        self.assertEqual(decision.difference, "0")

    def test_mismatch_is_reported(self):
        executor = ReconciliationExecutor()

        request = ReconciliationRequest(
            operation_id="EX016-EXEC-002",
            expected_amount="250",
            recorded_amount="240",
            unit="SHIR",
        )

        decision = executor.reconcile(request)

        self.assertEqual(decision.status, "MISMATCH")
        self.assertEqual(decision.difference, "-10")


if __name__ == "__main__":
    unittest.main()
