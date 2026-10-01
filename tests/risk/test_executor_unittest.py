import unittest

from financial_core.risk.contracts import RiskRequest
from financial_core.risk.executor import RiskExecutor


class TestRiskExecutor(unittest.TestCase):

    def test_approved_request_returns_approved_decision(self):
        executor = RiskExecutor(max_amount="1000")

        request = RiskRequest(
            operation_id="RISK-EXEC-001",
            settlement_type="INTERNAL",
            amount="500",
            unit="POINT",
        )

        decision = executor.evaluate(request)

        self.assertTrue(decision.approved)
        self.assertEqual(decision.operation_id, "RISK-EXEC-001")

    def test_limit_violation_returns_rejected_decision(self):
        executor = RiskExecutor(max_amount="1000")

        request = RiskRequest(
            operation_id="RISK-EXEC-002",
            settlement_type="ON_CHAIN",
            amount="1001",
            unit="2FUNC",
        )

        decision = executor.evaluate(request)

        self.assertFalse(decision.approved)
        self.assertEqual(
            decision.reason,
            "amount exceeds risk limit",
        )


if __name__ == "__main__":
    unittest.main()
