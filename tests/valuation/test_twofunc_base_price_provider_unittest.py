import unittest
from decimal import Decimal, localcontext

from financial_core.contracts.valuation import ValuationRequest
from financial_core.valuation.twofunc_base_price_provider import (
    TwofuncBasePriceProvider,
)


class TwofuncBasePriceProviderTests(unittest.TestCase):
    def setUp(self):
        self.provider = TwofuncBasePriceProvider()

    def make_request(
        self,
        asset="2FUNC",
        quote_asset="USD",
        timestamp="2026-11-13T00:00:00Z",
    ):
        return ValuationRequest(
            asset=asset,
            quote_asset=quote_asset,
            timestamp=timestamp,
            metadata={},
        )

    def test_returns_approved_base_price_at_high_decimal_precision(self):
        result = self.provider.get_value(self.make_request())

        with localcontext() as context:
            context.prec = self.provider.DECIMAL_PRECISION
            expected = Decimal(1) / Decimal(2_719_050)

        self.assertEqual(result.price, str(expected))
        self.assertEqual(result.asset, "2FUNC")
        self.assertEqual(result.quote_asset, "USD")
        self.assertEqual(result.source, "APPROVED_BASE_PRICE_POLICY")
        self.assertEqual(result.timestamp, "2026-11-13T00:00:00Z")

    def test_preserves_exact_ratio_and_distinguishes_base_from_market_price(self):
        result = self.provider.get_value(self.make_request())

        self.assertEqual(result.metadata["base_price_numerator"], "1")
        self.assertEqual(result.metadata["base_price_denominator"], "2719050")
        self.assertEqual(result.metadata["price_type"], "APPROVED_BASE_PRICE")
        self.assertEqual(result.metadata["valuation_mode"], "BASE_PRICE_MODE")
        self.assertFalse(result.metadata["market_price_available"])
        self.assertFalse(result.metadata["market_price_verified"])
        self.assertEqual(
            result.metadata["verification_scope"], "APPROVED_BASE_POLICY_ONLY"
        )
        self.assertTrue(result.verified)

    def test_rejects_assets_other_than_twofunc(self):
        with self.assertRaisesRegex(ValueError, "only 2FUNC"):
            self.provider.get_value(self.make_request(asset="BTC"))

    def test_rejects_quote_assets_other_than_usd(self):
        with self.assertRaisesRegex(ValueError, "only USD"):
            self.provider.get_value(self.make_request(quote_asset="USDT"))

    def test_rejects_empty_timestamp(self):
        with self.assertRaisesRegex(ValueError, "timestamp"):
            self.provider.get_value(self.make_request(timestamp=" "))


if __name__ == "__main__":
    unittest.main()
