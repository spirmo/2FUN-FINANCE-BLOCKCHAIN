import tempfile
import unittest
from pathlib import Path

from financial_core.contracts.idempotency import IdempotencyRecord
from financial_core.idempotency.generic_sqlite_store import (
    GenericSQLiteIdempotencyStore,
)


class TestGenericSQLiteIdempotencyStore(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.store = GenericSQLiteIdempotencyStore(
            Path(self.temp_dir.name) / "idempotency.db"
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def record(self, amount="500"):
        return IdempotencyRecord(
            operation_id="OP-100",
            operation_type="REWARD",
            result={"amount": amount, "unit": "Drika"},
        )

    def test_first_record_is_persisted(self):
        record = self.record()
        self.store.save("OP-100", record)

        self.assertEqual(self.store.get("OP-100"), record)

    def test_identical_record_can_be_saved_again(self):
        record = self.record()
        self.store.save("OP-100", record)
        self.store.save("OP-100", record)

        self.assertEqual(self.store.get("OP-100"), record)

    def test_conflicting_record_with_same_id_is_rejected(self):
        self.store.save("OP-100", self.record(amount="500"))

        with self.assertRaises(ValueError):
            self.store.save("OP-100", self.record(amount="900"))

        self.assertEqual(
            self.store.get("OP-100"),
            self.record(amount="500"),
        )

    def test_record_id_must_match_storage_key(self):
        with self.assertRaises(ValueError):
            self.store.save("OP-OTHER", self.record())

        self.assertIsNone(self.store.get("OP-OTHER"))


if __name__ == "__main__":
    unittest.main()
