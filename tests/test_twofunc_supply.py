import unittest

from financial_core.twofunc.supply import (
    BASE_UNITS_PER_2FUNC,
    BASE_UNITS_PER_DRIKA,
    COIN_DECIMALS,
    COIN_NAME,
    DRIKA_PER_2FUNC,
    ECOSYSTEM_NAME,
    MAX_SUPPLY,
    MAX_SUPPLY_BASE_UNITS,
    SupplyLimitError,
    SupplyState,
    base_units_to_drika,
    drika_to_base_units,
    whole_2func_to_base_units,
)


class TwoFuncSupplyTests(unittest.TestCase):
    def test_canonical_identity_and_supply_cap(self):
        self.assertEqual(ECOSYSTEM_NAME, "2FUN")
        self.assertEqual(COIN_NAME, "2FUNC")
        self.assertEqual(MAX_SUPPLY, 14_441_417_005_600)
        self.assertEqual(COIN_DECIMALS, 18)
        self.assertEqual(BASE_UNITS_PER_2FUNC, 10**18)
        self.assertEqual(
            MAX_SUPPLY_BASE_UNITS,
            MAX_SUPPLY * 10**18,
        )

    def test_denomination_ratios_are_exact(self):
        self.assertEqual(DRIKA_PER_2FUNC, 5_000)
        self.assertEqual(BASE_UNITS_PER_DRIKA, 200_000_000_000_000)
        self.assertEqual(drika_to_base_units(5_000), BASE_UNITS_PER_2FUNC)
        self.assertEqual(base_units_to_drika(BASE_UNITS_PER_2FUNC), 5_000)

    def test_whole_coin_conversion(self):
        self.assertEqual(
            whole_2func_to_base_units(2),
            2 * BASE_UNITS_PER_2FUNC,
        )

    def test_initial_state_has_full_supply_remaining(self):
        state = SupplyState()
        self.assertEqual(state.issued, 0)
        self.assertEqual(state.remaining, MAX_SUPPLY_BASE_UNITS)

    def test_valid_issuance_returns_new_state(self):
        original = SupplyState(issued=100)
        updated = original.issue(25)
        self.assertEqual(original.issued, 100)
        self.assertEqual(updated.issued, 125)
        self.assertEqual(updated.remaining, MAX_SUPPLY_BASE_UNITS - 125)

    def test_exact_cap_is_allowed(self):
        state = SupplyState().issue(MAX_SUPPLY_BASE_UNITS)
        self.assertEqual(state.issued, MAX_SUPPLY_BASE_UNITS)
        self.assertEqual(state.remaining, 0)

    def test_issuance_over_cap_is_rejected(self):
        with self.assertRaises(SupplyLimitError):
            SupplyState(issued=MAX_SUPPLY_BASE_UNITS).issue(1)

    def test_negative_or_zero_issuance_is_rejected(self):
        for amount in (0, -1):
            with self.subTest(amount=amount):
                with self.assertRaises(SupplyLimitError):
                    SupplyState().issue(amount)

    def test_invalid_issuance_types_are_rejected(self):
        for amount in (True, 1.5, "100"):
            with self.subTest(amount=amount):
                with self.assertRaises(TypeError):
                    SupplyState().issue(amount)

    def test_invalid_initial_supply_is_rejected(self):
        for issued in (-1, MAX_SUPPLY_BASE_UNITS + 1):
            with self.subTest(issued=issued):
                with self.assertRaises(SupplyLimitError):
                    SupplyState(issued=issued)

    def test_drika_conversion_rejects_invalid_amounts(self):
        for amount in (True, 1.5, "10"):
            with self.subTest(amount=amount):
                with self.assertRaises(TypeError):
                    drika_to_base_units(amount)
        with self.assertRaises(ValueError):
            drika_to_base_units(-1)

    def test_base_units_to_drika_rejects_fractional_drika(self):
        with self.assertRaises(ValueError):
            base_units_to_drika(1)


if __name__ == "__main__":
    unittest.main()
