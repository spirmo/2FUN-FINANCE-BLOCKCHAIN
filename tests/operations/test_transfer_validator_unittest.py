import unittest

from financial_core.contracts.transfer import TransferRequest
from financial_core.operations.transfer_validator import TransferValidator


class TestTransferValidator(unittest.TestCase):
    def setUp(self):
        self.validator = TransferValidator()

    def make_request(self, unit):
        return TransferRequest(
            operation_id="TR-001",
            source_account_id="ACC-001",
            destination_account_id="ACC-002",
            amount="10",
            unit=unit,
        )

    def test_transferable_unit_is_accepted(self):
        result = self.validator.validate(self.make_request("Drika"))
        self.assertTrue(result.valid)
        self.assertIsNone(result.reason)

    def test_activity_units_are_rejected(self):
        for unit in ("POINT", "XP"):
            with self.subTest(unit=unit):
                result = self.validator.validate(self.make_request(unit))
                self.assertFalse(result.valid)
                self.assertEqual(
                    result.reason,
                    "POINT is an activity unit and cannot be transferred",
                )


if __name__ == "__main__":
    unittest.main()
