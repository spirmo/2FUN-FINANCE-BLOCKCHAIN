import unittest

from financial_core.blockchain.adapter import BlockchainNetworkAdapter
from financial_core.blockchain.contracts import (
    BlockchainSubmissionRequest,
    BlockchainSubmissionResult,
)


class TestBlockchainNetworkAdapter(unittest.TestCase):

    def test_request_and_result_contracts(self):
        request = BlockchainSubmissionRequest(
            operation_id="BC001-001",
            amount="1",
            unit="2FUNC",
        )

        result = BlockchainSubmissionResult(
            operation_id="BC001-001",
            status="SUBMITTED",
            blockchain_tx_hash="0xabc123",
        )

        self.assertEqual(request.operation_id, "BC001-001")
        self.assertEqual(result.operation_id, "BC001-001")
        self.assertEqual(result.status, "SUBMITTED")
        self.assertEqual(result.blockchain_tx_hash, "0xabc123")

    def test_adapter_is_abstract_boundary(self):
        self.assertTrue(issubclass(
            BlockchainNetworkAdapter,
            object,
        ))

        with self.assertRaises(TypeError):
            BlockchainNetworkAdapter()


if __name__ == "__main__":
    unittest.main()
