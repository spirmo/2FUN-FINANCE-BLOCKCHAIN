import unittest

from financial_core.idempotency.contracts import IdempotencyDecision
from financial_core.idempotency.executor import IdempotencyExecutor


class TestIdempotencyExecutor(unittest.TestCase):

    def test_first_operation_is_accepted(self):
        executor = IdempotencyExecutor()

        decision = executor.check_and_register("EX015-001")

        self.assertIsInstance(decision, IdempotencyDecision)
        self.assertTrue(decision.accepted)
        self.assertIsNone(decision.reason)

    def test_duplicate_operation_is_rejected(self):
        executor = IdempotencyExecutor()

        executor.register(
            "EX015-002",
            "RESULT-002",
        )

        decision = executor.check("EX015-002")

        self.assertFalse(decision.accepted)
        self.assertEqual(
            decision.reason,
            "operation already processed",
        )

    def test_result_reference_is_preserved(self):
        executor = IdempotencyExecutor()

        executor.register(
            "EX015-003",
            "RESULT-003",
        )

        self.assertEqual(
            executor.result_reference("EX015-003"),
            "RESULT-003",
        )

    def test_empty_operation_id_is_rejected(self):
        executor = IdempotencyExecutor()

        decision = executor.check("")

        self.assertFalse(decision.accepted)
        self.assertEqual(
            decision.reason,
            "operation_id is required",
        )


if __name__ == "__main__":
    unittest.main()
