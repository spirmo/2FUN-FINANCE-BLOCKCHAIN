import unittest

from financial_core.blockchain.gateway import BlockchainSettlementGateway
from financial_core.settlement.contracts import SettlementRequest
from financial_core.settlement.executor import SettlementExecutor


class TestBlockchainSettlementGateway(unittest.TestCase):

    def test_on_chain_settlement_is_submitted_through_gateway(self):
        gateway = BlockchainSettlementGateway()
        executor = SettlementExecutor(blockchain_gateway=gateway)

        request = SettlementRequest(
            operation_id="EX012-ONCHAIN-001",
            settlement_type="ON_CHAIN",
            amount="1",
            unit="2FUNC",
            metadata={
                "destination": "TEST-ADDRESS",
            },
        )

        record = executor.execute(request)

        self.assertEqual(record.operation_id, "EX012-ONCHAIN-001")
        self.assertEqual(record.settlement_type, "ON_CHAIN")
        self.assertEqual(record.amount, "1")
        self.assertEqual(record.unit, "2FUNC")
        self.assertEqual(record.status, "SUBMITTED")
        self.assertEqual(
            record.metadata["settlement_mode"],
            "ON_CHAIN",
        )
        self.assertEqual(
            record.metadata["blockchain_status"],
            "PENDING_SUBMISSION",
        )
        self.assertEqual(
            record.metadata["destination"],
            "TEST-ADDRESS",
        )

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
