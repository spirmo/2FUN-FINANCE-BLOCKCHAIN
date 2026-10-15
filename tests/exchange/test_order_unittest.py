import unittest

from financial_core.exchange.order import Order


class TestOrder(unittest.TestCase):
    def make_order(self, order_id, side, quantity, price):
        return Order(
            order_id=order_id,
            market_id="2FUNC-USD",
            account_id="ACC-001",
            side=side,
            order_type="LIMIT",
            quantity=str(quantity),
            price=str(price),
        )


    def test_buy_order_creation(self):
        order = Order(
            order_id="ORD-001",
            market_id="2FUNC-USD",
            account_id="ACC-001",
            side="BUY",
            order_type="LIMIT",
            quantity="10",
            price="25.50",
        )

        self.assertEqual(order.order_id, "ORD-001")
        self.assertEqual(order.side, "BUY")
        self.assertEqual(order.status, "OPEN")

    def test_sell_order_creation(self):
        order = Order(
            order_id="ORD-002",
            market_id="2FUNC-USD",
            account_id="ACC-002",
            side="SELL",
            order_type="LIMIT",
            quantity="5",
            price="30",
        )

        self.assertEqual(order.side, "SELL")

    def test_rejects_invalid_side(self):
        with self.assertRaises(ValueError):
            Order(
                order_id="ORD-003",
                market_id="2FUNC-USD",
                account_id="ACC-003",
                side="INVALID",
                order_type="LIMIT",
                quantity="1",
                price="10",
            )

    def test_rejects_non_positive_quantity(self):
        with self.assertRaises(ValueError):
            Order(
                order_id="ORD-004",
                market_id="2FUNC-USD",
                account_id="ACC-004",
                side="BUY",
                order_type="LIMIT",
                quantity="0",
                price="10",
            )

    def test_rejects_non_positive_price(self):
        with self.assertRaises(ValueError):
            Order(
                order_id="ORD-005",
                market_id="2FUNC-USD",
                account_id="ACC-005",
                side="BUY",
                order_type="LIMIT",
                quantity="1",
                price="0",
            )


    def test_allows_valid_status_transitions(self):
        order = Order(
            order_id="ORD-007",
            market_id="2FUNC-USD",
            account_id="ACC-007",
            side="BUY",
            order_type="LIMIT",
            quantity="10",
            price="25",
        )

        partial = order.with_status("PARTIALLY_FILLED")
        filled = partial.with_status("FILLED")

        self.assertEqual(order.status, "OPEN")
        self.assertEqual(partial.status, "PARTIALLY_FILLED")
        self.assertEqual(filled.status, "FILLED")

    def test_rejects_invalid_status_transition(self):
        order = Order(
            order_id="ORD-008",
            market_id="2FUNC-USD",
            account_id="ACC-008",
            side="BUY",
            order_type="LIMIT",
            quantity="10",
            price="25",
        )

        with self.assertRaises(ValueError):
            order.with_status("CANCELLED").with_status("FILLED")

    def test_partial_fill_reduces_remaining_quantity(self):
        order = self.make_order("BUY-PARTIAL", "BUY", "10", "20")

        filled = order.with_fill("4")

        self.assertEqual(filled.quantity, "6")
        self.assertEqual(filled.status, "PARTIALLY_FILLED")
        self.assertEqual(order.quantity, "10")
        self.assertEqual(order.status, "OPEN")

    def test_full_fill_marks_order_filled(self):
        order = self.make_order("BUY-FULL", "BUY", "10", "20")

        filled = order.with_fill("10")

        self.assertEqual(filled.quantity, "0")
        self.assertEqual(filled.status, "FILLED")
        self.assertEqual(order.quantity, "10")
        self.assertEqual(order.status, "OPEN")

    def test_fill_cannot_exceed_remaining_quantity(self):
        order = self.make_order("BUY-OVERFILL", "BUY", "10", "20")

        with self.assertRaises(ValueError):
            order.with_fill("11")

    def test_fill_must_be_positive(self):
        order = self.make_order("BUY-ZERO", "BUY", "10", "20")

        with self.assertRaises(ValueError):
            order.with_fill("0")

    def test_rejects_invalid_status_transition_from_terminal_state(self):
        order = Order(
            order_id="ORD-009",
            market_id="2FUNC-USD",
            account_id="ACC-009",
            side="BUY",
            order_type="LIMIT",
            quantity="10",
            price="25",
        )

        filled = order.with_status("FILLED")

        with self.assertRaises(ValueError):
            filled.with_status("OPEN")

    def test_rejects_invalid_status(self):
        with self.assertRaises(ValueError):
            Order(
                order_id="ORD-006",
                market_id="2FUNC-USD",
                account_id="ACC-006",
                side="BUY",
                order_type="LIMIT",
                quantity="1",
                price="10",
                status="INVALID",
            )


if __name__ == "__main__":
    unittest.main()
