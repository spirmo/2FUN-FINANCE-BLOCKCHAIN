import unittest

from financial_core.blockchain.adapter import BlockchainNetworkAdapter
from financial_core.blockchain.contracts import (
    BlockchainSubmissionRequest,
    BlockchainSubmissionResult,
)
from financial_core.blockchain.gateway import BlockchainSettlementGateway
from financial_core.settlement.contracts import SettlementRequest
from financial_core.settlement.executor import SettlementExecutor


class TestBlockchainSettlementGateway(unittest.TestCase):
    def test_on_chain_settlement_is_pending_without_network_adapter(self):
        gateway = BlockchainSettlementGateway()
        executor = SettlementExecutor(blockchain_gateway=gateway)
        request = SettlementRequest(
            operation_id="EX012-ONCHAIN-001",
            settlement_type="ON_CHAIN",
            amount="1",
            unit="2FUNC",
            metadata={"destination": "TEST-ADDRESS"},
        )

        record = executor.execute(request)

        self.assertEqual(record.operation_id, request.operation_id)
        self.assertEqual(record.settlement_type, "ON_CHAIN")
        self.assertEqual(record.amount, "1")
        self.assertEqual(record.unit, "2FUNC")
        self.assertEqual(record.status, "SUBMITTED")
        self.assertEqual(record.metadata["settlement_mode"], "ON_CHAIN")
        self.assertEqual(
            record.metadata["blockchain_status"], "PENDING_SUBMISSION"
        )
        self.assertTrue(record.transaction_reference.startswith("bc-submit-"))
        self.assertEqual(
            record.metadata["submission_reference"], record.transaction_reference
        )
        self.assertIsNone(record.metadata["blockchain_tx_hash"])
        self.assertIsNone(
            record.metadata["transaction_identity"].blockchain_tx_hash
        )
        self.assertEqual(record.metadata["destination"], "TEST-ADDRESS")

    def test_network_adapter_result_is_propagated(self):
        class FakeAdapter(BlockchainNetworkAdapter):
            def submit(self, request: BlockchainSubmissionRequest):
                self.request = request
                return BlockchainSubmissionResult(
                    operation_id=request.operation_id,
                    status="CONFIRMED",
                    blockchain_tx_hash="0xrealhash",
                    metadata={"confirmations": 3},
                )

        adapter = FakeAdapter()
        gateway = BlockchainSettlementGateway(network_adapter=adapter)
        executor = SettlementExecutor(blockchain_gateway=gateway)
        request = SettlementRequest(
            operation_id="EX012-ADAPTER-001",
            settlement_type="ON_CHAIN",
            amount="2",
            unit="2FUNC",
            metadata={"destination": "TEST-ADDRESS"},
        )

        record = executor.execute(request)

        self.assertEqual(adapter.request.operation_id, request.operation_id)
        self.assertEqual(adapter.request.amount, "2")
        self.assertEqual(record.status, "SUBMITTED")
        self.assertEqual(record.metadata["blockchain_status"], "SUBMITTED")
        self.assertEqual(
            record.metadata["adapter_reported_status"], "CONFIRMED"
        )
        self.assertEqual(record.metadata["blockchain_tx_hash"], "0xrealhash")
        self.assertEqual(record.transaction_reference, "0xrealhash")
        self.assertEqual(record.metadata["confirmations"], 3)
        self.assertEqual(
            record.metadata["transaction_identity"].blockchain_tx_hash,
            "0xrealhash",
        )

    def test_mismatched_adapter_operation_id_is_rejected(self):
        class MismatchedAdapter(BlockchainNetworkAdapter):
            def submit(self, request: BlockchainSubmissionRequest):
                return BlockchainSubmissionResult(
                    operation_id="SOME-OTHER-OPERATION",
                    status="CONFIRMED",
                    blockchain_tx_hash="0xwrong",
                )

        gateway = BlockchainSettlementGateway(
            network_adapter=MismatchedAdapter()
        )
        request = SettlementRequest(
            operation_id="EX012-ADAPTER-002",
            settlement_type="ON_CHAIN",
            amount="1",
            unit="2FUNC",
        )

        with self.assertRaisesRegex(ValueError, "mismatched operation_id"):
            gateway.settle(request)

    def test_on_chain_requires_blockchain_gateway(self):
        executor = SettlementExecutor()
        request = SettlementRequest(
            operation_id="EX012-ONCHAIN-002",
            settlement_type="ON_CHAIN",
            amount="1",
            unit="2FUNC",
        )

        with self.assertRaises(RuntimeError):
            executor.execute(request)


if __name__ == "__main__":
    unittest.main()
