import unittest

from financial_core.idempotency.executor import IdempotencyExecutor


class TestIdempotencyE2E(unittest.TestCase):

    def test_duplicate_request_does_not_execute_twice(self):
        executor = IdempotencyExecutor()

        execution_count = 0

        first = executor.check("EX015-E2E-001")

        self.assertTrue(first.accepted)

        # Simulated business execution.
        execution_count += 1
        result_reference = "RESULT-EX015-001"

        executor.register(
            "EX015-E2E-001",
            result_reference,
        )

        second = executor.check("EX015-E2E-001")

        self.assertFalse(second.accepted)
        self.assertEqual(
            second.reason,
            "operation already processed",
        )

        # Duplicate request must not execute business logic again.
        self.assertEqual(execution_count, 1)

        # Previous result remains recoverable.
        self.assertEqual(
            executor.result_reference("EX015-E2E-001"),
            "RESULT-EX015-001",
        )


if __name__ == "__main__":
    unittest.main()
