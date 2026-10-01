"""EX-002 Market tests."""

import pytest

from financial_core.exchange.market import Market


def test_market_creation():
    market = Market(
        market_id="2FUNC-USD",
        base_unit="2FUNC",
        quote_unit="USD",
        price_precision=8,
        quantity_precision=8,
        min_quantity="0.00000001",
    )

    assert market.market_id == "2FUNC-USD"
    assert market.base_unit == "2FUNC"
    assert market.quote_unit == "USD"
    assert market.symbol == "2FUNC/USD"
    assert market.status == "ACTIVE"
    assert market.is_active is True


def test_market_rejects_same_base_and_quote():
    with pytest.raises(ValueError, match="must differ"):
        Market(
            market_id="INVALID",
            base_unit="2FUNC",
            quote_unit="2FUNC",
        )


def test_market_rejects_invalid_status():
    with pytest.raises(ValueError, match="invalid market status"):
        Market(
            market_id="2FUNC-USD",
            base_unit="2FUNC",
            quote_unit="USD",
            status="UNKNOWN",
        )


def test_market_rejects_negative_min_quantity():
    with pytest.raises(ValueError, match="cannot be negative"):
        Market(
            market_id="2FUNC-USD",
            base_unit="2FUNC",
            quote_unit="USD",
            min_quantity="-1",
        )


def test_market_can_be_suspended():
    market = Market(
        market_id="2FUNC-USD",
        base_unit="2FUNC",
        quote_unit="USD",
        status="SUSPENDED",
    )

    assert market.is_active is False
