import unittest

from financial_core.liquidity.contracts import LiquidityPool
from financial_core.liquidity.validator import LiquidityValidator


class TestLiquidityValidator(unittest.TestCase):

    def setUp(self):
        self.validator = LiquidityValidator()

    def test_valid_pool_is_approved(self):
        pool = LiquidityPool(
            pool_id="POOL-001",
            market_id="2FUNC-SHIR",
            base_unit="2FUNC",
            quote_unit="SHIR",
            base_reserve="100",
            quote_reserve="2000",
        )

        decision = self.validator.validate(pool)

        self.assertTrue(decision.approved)
        self.assertIsNone(decision.reason)

    def test_same_units_are_rejected(self):
        pool = LiquidityPool(
            pool_id="POOL-002",
            market_id="INVALID",
            base_unit="POINT",
            quote_unit="POINT",
            base_reserve="100",
            quote_reserve="100",
        )

        decision = self.validator.validate(pool)

        self.assertFalse(decision.approved)

    def test_zero_reserve_is_rejected(self):
        pool = LiquidityPool(
            pool_id="POOL-003",
            market_id="2FUNC-SHIR",
            base_unit="2FUNC",
            quote_unit="SHIR",
            base_reserve="0",
            quote_reserve="2000",
        )

        decision = self.validator.validate(pool)

        self.assertFalse(decision.approved)

    def test_invalid_reserve_is_rejected(self):
        pool = LiquidityPool(
            pool_id="POOL-004",
            market_id="2FUNC-SHIR",
            base_unit="2FUNC",
            quote_unit="SHIR",
            base_reserve="invalid",
            quote_reserve="2000",
        )

        decision = self.validator.validate(pool)

        self.assertFalse(decision.approved)


if __name__ == "__main__":
    unittest.main()
