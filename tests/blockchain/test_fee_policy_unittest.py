"""Tests for the configurable network fee policy."""

import unittest

from financial_core.blockchain.fee_policy import FeePolicy
from financial_core.blockchain.twofunc_supply import drika_to_base_units


class TestFeePolicy(unittest.TestCase):
    def setUp(self):
        # Test-only values; these are not proposed production network rates.
        self.policy = FeePolicy(
            base_fee_drika={
                "TRANSFER": 10,
                "CONTRACT": 20,
            },
            price_per_resource_unit_drika=2,
            max_fee_drika=100,
        )

    def test_calculates_base_plus_resource_cost(self):
        quote = self.policy.quote(
            operation_type="TRANSFER",
            resource_units=5,
        )

        self.assertEqual(quote.fee_drika, 20)
        self.assertEqual(
            quote.fee_base_units,
            drika_to_base_units(20),
        )

    def test_operation_can_have_a_different_base_fee(self):
        quote = self.policy.quote(
            operation_type="CONTRACT",
            resource_units=5,
        )

        self.assertEqual(quote.fee_drika, 30)

    def test_zero_resource_units_are_valid(self):
        quote = self.policy.quote(
            operation_type="TRANSFER",
            resource_units=0,
        )

        self.assertEqual(quote.fee_drika, 10)

    def test_rejects_unknown_operation(self):
        with self.assertRaises(ValueError):
            self.policy.quote(
                operation_type="UNKNOWN",
                resource_units=1,
            )

    def test_rejects_negative_resource_units(self):
        with self.assertRaises(ValueError):
            self.policy.quote(
                operation_type="TRANSFER",
                resource_units=-1,
            )

    def test_rejects_boolean_resource_units(self):
        with self.assertRaises(ValueError):
            self.policy.quote(
                operation_type="TRANSFER",
                resource_units=True,
            )

    def test_rejects_fee_above_maximum_instead_of_silently_capping(self):
        with self.assertRaises(ValueError):
            self.policy.quote(
                operation_type="CONTRACT",
                resource_units=41,
            )

    def test_rejects_negative_base_fee(self):
        with self.assertRaises(ValueError):
            FeePolicy(
                base_fee_drika={"TRANSFER": -1},
                price_per_resource_unit_drika=1,
                max_fee_drika=100,
            )

    def test_rejects_negative_resource_price(self):
        with self.assertRaises(ValueError):
            FeePolicy(
                base_fee_drika={"TRANSFER": 1},
                price_per_resource_unit_drika=-1,
                max_fee_drika=100,
            )

    def test_rejects_base_fee_above_maximum(self):
        with self.assertRaises(ValueError):
            FeePolicy(
                base_fee_drika={"TRANSFER": 101},
                price_per_resource_unit_drika=1,
                max_fee_drika=100,
            )


if __name__ == "__main__":
    unittest.main()
