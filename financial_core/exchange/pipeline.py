"""End-to-end exchange execution pipeline."""

from dataclasses import dataclass
from decimal import Decimal

from financial_core.exchange.contracts import ExchangeRequest
from financial_core.exchange.fee import FeeCalculator, FeeResult
from financial_core.idempotency.contracts import IdempotencyDecision
from financial_core.idempotency.executor import IdempotencyExecutor
from financial_core.risk.contracts import RiskDecision, RiskRequest
from financial_core.risk.executor import RiskExecutor
from financial_core.settlement.contracts import SettlementRequest, SettlementRecord
from financial_core.settlement.executor import SettlementExecutor
from financial_core.reconciliation.contracts import ReconciliationRequest, ReconciliationDecision
from financial_core.reconciliation.executor import ReconciliationExecutor
from financial_core.exchange.matching import MatchResult, MatchingEngine
from financial_core.exchange.order import Order
from financial_core.exchange.order_book import OrderBook
from financial_core.exchange.trade import Trade
from financial_core.contracts.uvi import UVIValueRequest, UVIValueResult
from financial_core.integrations.uvi_exchange_adapter import UVIExchangeAdapter
from platform_core.universal_value.ledger.value_ledger import ValueLedger


@dataclass(frozen=True)
class ExchangePipelineResult:
    """Result of the market execution portion of an exchange."""

    match: MatchResult
    trade: Trade
    fee: FeeResult
    operation_id: str | None = None
    risk_decision: RiskDecision | None = None
    idempotency_decision: IdempotencyDecision | None = None
    uvi_result: UVIValueResult | None = None
    settlement_record: SettlementRecord | None = None
    reconciliation_decision: ReconciliationDecision | None = None


class ExchangePipeline:
    """
    Coordinate existing Exchange market components.

    This class owns orchestration only.
    Market, order book, matching, trade, and fee rules remain
    owned by their existing domain components.
    """

    def __init__(
        self,
        fee_rate: Decimal | str,
        uvi_ledger: ValueLedger,
    ):
        self._matching = MatchingEngine()
        self._fees = FeeCalculator(fee_rate)
        self._risk = RiskExecutor()
        self._idempotency = IdempotencyExecutor()
        self._uvi = UVIExchangeAdapter(uvi_ledger)
        self._settlement = SettlementExecutor()
        self._reconciliation = ReconciliationExecutor()

    def execute(
        self,
        request: ExchangeRequest,
        buy_order: Order,
        sell_order: Order,
    ) -> ExchangePipelineResult:
        """Run idempotency and risk gates before market execution."""

        idempotency_decision = self._idempotency.check_and_register(
            request.operation_id
        )

        if not idempotency_decision.accepted:
            raise ValueError(idempotency_decision.reason)

        risk_decision = self._risk.evaluate(
            RiskRequest(
                operation_id=request.operation_id,
                settlement_type="INTERNAL",
                amount=request.source_amount,
                unit=request.source_unit,
                metadata=dict(request.metadata),
            )
        )

        if not risk_decision.approved:
            raise ValueError(risk_decision.reason)

        market_result = self.execute_market(
            buy_order=buy_order,
            sell_order=sell_order,
        )

        uvi_result = self._uvi.process(
            UVIValueRequest(
                operation_id=request.operation_id,
                user_id=request.user_id,
                unit=request.source_unit,
                amount=request.source_amount,
                metadata=dict(request.metadata),
            ),
            target_unit=request.target_unit,
            quoted_target_amount=request.quoted_target_amount,
            conversion_rate=request.conversion_rate,
        )

        settlement_record = self._settlement.execute(
            SettlementRequest(
                operation_id=request.operation_id,
                settlement_type="INTERNAL",
                amount=uvi_result.metadata["target_amount"],
                unit=uvi_result.metadata["target_unit"],
                metadata={
                    **dict(request.metadata),
                    "source": "EX-017",
                    "uvi_status": uvi_result.status,
                    "uvi_recorded": uvi_result.recorded,
                },
            )
        )

        reconciliation_decision = self._reconciliation.reconcile(
            ReconciliationRequest(
                operation_id=request.operation_id,
                expected_amount=settlement_record.amount,
                recorded_amount=settlement_record.amount,
                unit=settlement_record.unit,
                metadata={
                    **dict(request.metadata),
                    "source": "EX-017",
                    "settlement_status": settlement_record.status,
                },
            )
        )

        return ExchangePipelineResult(
            match=market_result.match,
            trade=market_result.trade,
            fee=market_result.fee,
            operation_id=request.operation_id,
            risk_decision=risk_decision,
            idempotency_decision=idempotency_decision,
            uvi_result=uvi_result,
            settlement_record=settlement_record,
            reconciliation_decision=reconciliation_decision,
        )

    def execute_market(
        self,
        buy_order: Order,
        sell_order: Order,
    ) -> ExchangePipelineResult:
        """Add orders, match them, create a trade, and calculate fee."""

        order_book = OrderBook(market_id=buy_order.market_id)
        order_book.add_order(buy_order)
        order_book.add_order(sell_order)

        match = self._matching.match(order_book)

        if match is None:
            raise ValueError("orders could not be matched")

        trade_id = f"TRADE:{match.buy_order.order_id}:{match.sell_order.order_id}"
        trade = Trade.from_match_result(
            trade_id=trade_id,
            match=match,
        )
        fee = self._fees.calculate(trade)

        return ExchangePipelineResult(
            match=match,
            trade=trade,
            fee=fee,
        )
