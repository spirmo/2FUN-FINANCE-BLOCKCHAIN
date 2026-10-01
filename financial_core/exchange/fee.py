"""Exchange fee calculation domain."""

from dataclasses import dataclass
from decimal import Decimal

from financial_core.exchange.trade import Trade


@dataclass(frozen=True)
class FeeResult:
    """Calculated fee for an exchange trade."""

    trade_id: str
    fee_rate: Decimal
    fee_amount: Decimal


class FeeCalculator:
    """Calculate exchange fees from trade notional value."""

    def __init__(self, fee_rate: Decimal | str):
        rate = Decimal(str(fee_rate))

        if rate < 0:
            raise ValueError("fee_rate cannot be negative")

        self._fee_rate = rate

    @property
    def fee_rate(self) -> Decimal:
        """Return the configured fee rate."""

        return self._fee_rate

    def calculate(self, trade: Trade) -> FeeResult:
        """Calculate the fee for a trade."""

        fee_amount = trade.notional * self._fee_rate

        return FeeResult(
            trade_id=trade.trade_id,
            fee_rate=self._fee_rate,
            fee_amount=fee_amount,
        )
