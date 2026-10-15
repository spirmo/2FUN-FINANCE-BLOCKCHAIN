"""Native 2FUNC supply and exact denomination arithmetic."""

from dataclasses import dataclass

COIN_NAME = "2FUNC"
ECOSYSTEM_NAME = "2FUN"

# Maximum supply expressed in whole 2FUNC coins.
MAX_SUPPLY = 14_441_417_005_600

# Native coin precision: 18 decimal places.
COIN_DECIMALS = 18
BASE_UNITS_PER_2FUNC = 10**COIN_DECIMALS

# Economic denomination.
DRIKA_PER_2FUNC = 5_000

# Exact integer conversion: 1 Drika = 2 * 10**14 base units.
BASE_UNITS_PER_DRIKA = (
    BASE_UNITS_PER_2FUNC // DRIKA_PER_2FUNC
)

# The same supply cap represented in native base units.
MAX_SUPPLY_BASE_UNITS = MAX_SUPPLY * BASE_UNITS_PER_2FUNC


class SupplyLimitError(ValueError):
    """Raised when an issuance request violates the supply cap."""


def drika_to_base_units(amount: int) -> int:
    """Convert whole Drika to native base units exactly."""
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise TypeError("Drika amount must be an integer")
    if amount < 0:
        raise ValueError("Drika amount cannot be negative")
    return amount * BASE_UNITS_PER_DRIKA


def base_units_to_drika(amount: int) -> int:
    """Convert base units to whole Drika without rounding."""
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise TypeError("base-unit amount must be an integer")
    if amount < 0:
        raise ValueError("base-unit amount cannot be negative")
    if amount % BASE_UNITS_PER_DRIKA:
        raise ValueError("amount is not an exact whole-Drika value")
    return amount // BASE_UNITS_PER_DRIKA


def whole_2func_to_base_units(amount: int) -> int:
    """Convert whole 2FUNC coins to native base units."""
    if isinstance(amount, bool) or not isinstance(amount, int):
        raise TypeError("2FUNC amount must be an integer")
    if amount < 0:
        raise ValueError("2FUNC amount cannot be negative")
    return amount * BASE_UNITS_PER_2FUNC


@dataclass(frozen=True)
class SupplyState:
    """Cumulative issued supply measured in native base units."""

    issued: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.issued, bool) or not isinstance(self.issued, int):
            raise TypeError("issued supply must be an integer base-unit amount")
        if self.issued < 0:
            raise SupplyLimitError("issued supply cannot be negative")
        if self.issued > MAX_SUPPLY_BASE_UNITS:
            raise SupplyLimitError("issued supply exceeds the maximum supply")

    @property
    def remaining(self) -> int:
        """Return remaining supply in native base units."""
        return MAX_SUPPLY_BASE_UNITS - self.issued

    def issue(self, amount: int) -> "SupplyState":
        """Validate supply arithmetic only; this does not mint coins."""
        if isinstance(amount, bool) or not isinstance(amount, int):
            raise TypeError("issuance amount must be an integer base-unit amount")
        if amount <= 0:
            raise SupplyLimitError("issuance amount must be positive")
        if amount > self.remaining:
            raise SupplyLimitError("issuance would exceed the maximum supply")
        return SupplyState(issued=self.issued + amount)
