"""Approved pre-listing base-price policy for 2FUNC.

This provider exposes the approved base-price reference only. It is not a
market-price oracle and must not be used as a post-listing market quote.
"""

from decimal import Decimal, localcontext
from typing import Any

from financial_core.contracts.valuation import ValuationRequest, ValuationResult


class TwofuncBasePriceProvider:
    """Return the approved 2FUNC/USD base-price reference before listing."""

    ASSET = "2FUNC"
    QUOTE_ASSET = "USD"
    BASE_PRICE_NUMERATOR = 1
    BASE_PRICE_DENOMINATOR = 2_719_050
    DECIMAL_PRECISION = 80
    SOURCE = "APPROVED_BASE_PRICE_POLICY"

    def get_value(self, request: ValuationRequest) -> ValuationResult:
        if request.asset != self.ASSET:
            raise ValueError("TwofuncBasePriceProvider supports only 2FUNC")
        if request.quote_asset != self.QUOTE_ASSET:
            raise ValueError("TwofuncBasePriceProvider supports only USD quotes")
        if not isinstance(request.timestamp, str) or not request.timestamp.strip():
            raise ValueError("valuation timestamp must be a non-empty string")

        # Exact approved ratio: 1 / 2,719,050 USD per 2FUNC.
        # The contract carries a decimal string, so retain the exact ratio
        # separately and expose an 80-digit decimal representation.
        with localcontext() as context:
            context.prec = self.DECIMAL_PRECISION
            price = Decimal(self.BASE_PRICE_NUMERATOR) / Decimal(
                self.BASE_PRICE_DENOMINATOR
            )

        metadata: dict[str, Any] = {
            "valuation_mode": "BASE_PRICE_MODE",
            "price_type": "APPROVED_BASE_PRICE",
            "base_price_numerator": str(self.BASE_PRICE_NUMERATOR),
            "base_price_denominator": str(self.BASE_PRICE_DENOMINATOR),
            "market_price_available": False,
            "market_price_verified": False,
            "listing_status": "NOT_LISTED",
            "verification_scope": "APPROVED_BASE_POLICY_ONLY",
            "decimal_precision": self.DECIMAL_PRECISION,
            "decimal_representation": (
                "High-precision finite Decimal representation; the exact rate "
                "is the numerator divided by the denominator in this metadata."
            ),
        }

        return ValuationResult(
            asset=request.asset,
            quote_asset=request.quote_asset,
            price=str(price),
            timestamp=request.timestamp,
            source=self.SOURCE,
            # Verified policy reference, not a verified market quote.
            verified=True,
            metadata=metadata,
        )
