"""Deterministic, configurable network fee policy denominated in Drika."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from financial_core.blockchain.twofunc_supply import drika_to_base_units


@dataclass(frozen=True)
class FeeQuote:
    """A calculated fee; no funds are charged by creating this quote."""

    operation_type: str
    resource_units: int
    fee_drika: int
    fee_base_units: int


class FeePolicy:
    """
    Calculate network fees without mutating balances.

    Formula:
        fee_drika = base_fee_drika[operation_type]
                    + resource_units * price_per_resource_unit_drika

    All rates must be supplied explicitly by the caller.
    Exceeding the configured maximum rejects the quote; it never silently
    caps or rounds the calculated fee.
    """

    def __init__(
        self,
        *,
        base_fee_drika: Mapping[str, int],
        price_per_resource_unit_drika: int,
        max_fee_drika: int,
    ) -> None:
        if not isinstance(base_fee_drika, Mapping) or not base_fee_drika:
            raise ValueError("base_fee_drika must be a non-empty mapping")

        checked_base_fees = {}

        for operation_type, amount in base_fee_drika.items():
            if not isinstance(operation_type, str) or not operation_type.strip():
                raise ValueError("operation types must be non-empty strings")

            if isinstance(amount, bool) or not isinstance(amount, int):
                raise ValueError("base fees must be integers")

            if amount < 0:
                raise ValueError("base fees cannot be negative")

            checked_base_fees[operation_type] = amount

        if (
            isinstance(price_per_resource_unit_drika, bool)
            or not isinstance(price_per_resource_unit_drika, int)
            or price_per_resource_unit_drika < 0
        ):
            raise ValueError(
                "price_per_resource_unit_drika must be a non-negative integer"
            )

        if (
            isinstance(max_fee_drika, bool)
            or not isinstance(max_fee_drika, int)
            or max_fee_drika <= 0
        ):
            raise ValueError("max_fee_drika must be a positive integer")

        if any(fee > max_fee_drika for fee in checked_base_fees.values()):
            raise ValueError("base fee cannot exceed max_fee_drika")

        self._base_fee_drika = MappingProxyType(checked_base_fees)
        self._price_per_resource_unit_drika = (
            price_per_resource_unit_drika
        )
        self._max_fee_drika = max_fee_drika

    def quote(
        self,
        *,
        operation_type: str,
        resource_units: int,
    ) -> FeeQuote:
        """Calculate a fee quote without charging or recording a transaction."""

        if not isinstance(operation_type, str) or not operation_type.strip():
            raise ValueError("operation_type is required")

        if operation_type not in self._base_fee_drika:
            raise ValueError("unsupported operation type")

        if (
            isinstance(resource_units, bool)
            or not isinstance(resource_units, int)
            or resource_units < 0
        ):
            raise ValueError("resource_units must be a non-negative integer")

        fee_drika = (
            self._base_fee_drika[operation_type]
            + resource_units * self._price_per_resource_unit_drika
        )

        if fee_drika > self._max_fee_drika:
            raise ValueError("calculated fee exceeds max_fee_drika")

        return FeeQuote(
            operation_type=operation_type,
            resource_units=resource_units,
            fee_drika=fee_drika,
            fee_base_units=drika_to_base_units(fee_drika),
        )
