import unittest

from financial_core.liquidity.contracts import LiquidityPool
from financial_core.liquidity.executor import LiquidityExecutor


class TestLiquidityExecutor(unittest.TestCase):

    def test_register_and_get_pool(self):
        executor = LiquidityExecutor()

        pool = LiquidityPool(
            pool_id="POOL-001",
            market_id="2FUNC-SHIR",
            base_unit="2FUNC",
            quote_unit="SHIR",
            base_reserve="100",
            quote_reserve="2000",
        )

        decision = executor.register(pool)

        self.assertTrue(decision.approved)
        self.assertEqual(executor.get("POOL-001"), pool)
        self.assertEqual(executor.all_pools(), (pool,))

    def test_duplicate_pool_is_rejected(self):
        executor = LiquidityExecutor()

        pool = LiquidityPool(
            pool_id="POOL-002",
            market_id="2FUNC-SHIR",
            base_unit="2FUNC",
            quote_unit="SHIR",
            base_reserve="100",
            quote_reserve="2000",
        )

        executor.register(pool)

        with self.assertRaises(ValueError):
            executor.register(pool)

    def test_invalid_pool_is_rejected(self):
        executor = LiquidityExecutor()

        pool = LiquidityPool(
            pool_id="POOL-003",
            market_id="2FUNC-SHIR",
            base_unit="2FUNC",
            quote_unit="SHIR",
            base_reserve="0",
            quote_reserve="2000",
        )

        with self.assertRaises(ValueError):
            executor.register(pool)

        self.assertIsNone(executor.get("POOL-003"))
        self.assertEqual(executor.all_pools(), ())


if __name__ == "__main__":
    unittest.main()
