from financial_core.settlement import (
    BlockchainGateway,
    SettlementExecutor,
    SettlementRecord,
    SettlementRequest,
)


class FakeBlockchainGateway(BlockchainGateway):
    def settle(self, request):
        return SettlementRecord(
            operation_id=request.operation_id,
            settlement_type=request.settlement_type,
            amount=request.amount,
            unit=request.unit,
            status="CONFIRMED",
            transaction_reference="test-chain-tx",
        )


def test_internal_settlement():
    executor = SettlementExecutor()

    result = executor.execute(
        SettlementRequest(
            operation_id="op-internal-001",
            settlement_type="INTERNAL",
            amount="100",
            unit="POINT",
        )
    )

    assert result.status == "SETTLED"
    assert result.settlement_type == "INTERNAL"
    assert result.transaction_reference is None


def test_on_chain_settlement_uses_gateway():
    executor = SettlementExecutor(FakeBlockchainGateway())

    result = executor.execute(
        SettlementRequest(
            operation_id="op-chain-001",
            settlement_type="ON_CHAIN",
            amount="1",
            unit="2FUNC",
        )
    )

    assert result.status == "CONFIRMED"
    assert result.transaction_reference == "test-chain-tx"


def test_on_chain_requires_gateway():
    executor = SettlementExecutor()

    try:
        executor.execute(
            SettlementRequest(
                operation_id="op-chain-002",
                settlement_type="ON_CHAIN",
                amount="1",
                unit="2FUNC",
            )
        )
    except RuntimeError as exc:
        assert "BlockchainGateway" in str(exc)
    else:
        raise AssertionError("Expected RuntimeError")
