import unittest

from financial_core.risk.contracts import RiskRequest
from financial_core.risk.validator import RiskValidator


class TestRiskValidator(unittest.TestCase):

    def setUp(self):
        self.validator = RiskValidator(max_amount="1000")

    def test_valid_operation_is_approved(self):
        request = RiskRequest(
            operation_id="RISK-001",
            settlement_type="INTERNAL",
            amount="500",
            unit="POINT",
        )

        decision = self.validator.validate(request)

        self.assertTrue(decision.approved)
        self.assertIsNone(decision.reason)

    def test_amount_above_limit_is_rejected(self):
        request = RiskRequest(
            operation_id="RISK-002",
            settlement_type="INTERNAL",
            amount="1001",
            unit="POINT",
        )

        decision = self.validator.validate(request)

        self.assertFalse(decision.approved)
        self.assertEqual(
            decision.reason,
            "amount exceeds risk limit",
        )

    def test_invalid_settlement_type_is_rejected(self):
        request = RiskRequest(
            operation_id="RISK-003",
            settlement_type="UNKNOWN",
            amount="100",
            unit="POINT",
        )

        decision = self.validator.validate(request)

        self.assertFalse(decision.approved)

    def test_zero_amount_is_rejected(self):
        request = RiskRequest(
            operation_id="RISK-004",
            settlement_type="INTERNAL",
            amount="0",
            unit="POINT",
        )

        decision = self.validator.validate(request)

        self.assertFalse(decision.approved)

    def test_invalid_amount_is_rejected(self):
        request = RiskRequest(
            operation_id="RISK-005",
            settlement_type="INTERNAL",
            amount="invalid",
            unit="POINT",
        )

        decision = self.validator.validate(request)

        self.assertFalse(decision.approved)


if __name__ == "__main__":
    unittest.main()
