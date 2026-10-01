"""End-to-end price-adjusted reward executor."""

from decimal import Decimal

from financial_core.contracts.idempotency import IdempotencyRecord
from financial_core.contracts.integrity import IntegrityRequest
from financial_core.contracts.reward_execution import (
    RewardExecutionRequest,
    RewardExecutionResult,
)
from financial_core.contracts.uvi import UVIValueRequest
from financial_core.idempotency.generic_sqlite_store import (
    GenericSQLiteIdempotencyStore,
)
from financial_core.integrations.integrity_adapter import (
    UniversalIntegrityAdapter,
)
from financial_core.integrations.uvi_earn_adapter import UVIEarnAdapter
from financial_core.rewards.calculator import PriceAdjustedRewardCalculator


class RewardExecutor:
    """Execute a complete value-aware reward path.

    Financial state remains owned by UVI.
    Idempotency owns execution identity only.
    Universal Integrity owns hash generation.
    """

    def __init__(
        self,
        valuation_provider,
        uvi_adapter: UVIEarnAdapter,
        idempotency_store: GenericSQLiteIdempotencyStore,
        integrity_provider: UniversalIntegrityAdapter | None = None,
    ):
        self._valuation_provider = valuation_provider
        self._uvi_adapter = uvi_adapter
        self._idempotency_store = idempotency_store
        self._integrity_provider = (
            integrity_provider or UniversalIntegrityAdapter()
        )
        self._calculator = PriceAdjustedRewardCalculator()

    def execute(
        self,
        request: RewardExecutionRequest,
    ) -> RewardExecutionResult:

        existing = self._idempotency_store.get(request.operation_id)

        if existing is not None:
            data = existing.result

            return RewardExecutionResult(
                operation_id=data["operation_id"],
                user_id=data["user_id"],
                status=data["status"],
                base_reward=Decimal(data["base_reward"]),
                adjusted_reward=Decimal(data["adjusted_reward"]),
                reference_price=Decimal(data["reference_price"]),
                current_price=Decimal(data["current_price"]),
                adjustment_factor=Decimal(data["adjustment_factor"]),
                reward_unit=data["reward_unit"],
                valuation_asset=data["valuation_asset"],
                quote_asset=data["quote_asset"],
                uvi_transaction_id=data["uvi_transaction_id"],
                integrity_hash=data["integrity_hash"],
                idempotent=True,
                metadata=dict(data.get("metadata", {})),
            )

        calculation = self._calculator.calculate(
            request=__import__(
                "financial_core.contracts.reward",
                fromlist=["RewardCalculationRequest"],
            ).RewardCalculationRequest(
                operation_id=request.operation_id,
                base_reward=request.base_reward,
                reference_price=request.reference_price,
                current_price=request.current_price,
                reward_unit=request.reward_unit,
                valuation_asset=request.valuation_asset,
                quote_asset=request.quote_asset,
                metadata=request.metadata,
            )
        )

        integrity_request = IntegrityRequest(
            operation_id=request.operation_id,
            operation_type="REWARD",
            source="FINANCIAL_CORE",
            actor=request.user_id,
            origin="REWARD_EXECUTOR",
            target=request.valuation_asset,
            payload={
                "base_reward": str(calculation.base_reward),
                "adjusted_reward": str(calculation.adjusted_reward),
                "reference_price": str(calculation.reference_price),
                "current_price": str(calculation.current_price),
                "adjustment_factor": str(
                    calculation.adjustment_factor
                ),
                "reward_unit": calculation.reward_unit,
                "valuation_asset": calculation.valuation_asset,
                "quote_asset": calculation.quote_asset,
            },
            value=str(calculation.adjusted_reward),
        )

        integrity = self._integrity_provider.generate(
            integrity_request
        )

        uvi_result = self._uvi_adapter.process(
            UVIValueRequest(
                operation_id=request.operation_id,
                user_id=request.user_id,
                amount=str(calculation.adjusted_reward),
                unit=calculation.reward_unit,
                metadata={
                    **dict(request.metadata or {}),
                    "operation_type": "REWARD",
                    "valuation_asset": calculation.valuation_asset,
                    "quote_asset": calculation.quote_asset,
                    "reference_price": str(
                        calculation.reference_price
                    ),
                    "current_price": str(
                        calculation.current_price
                    ),
                    "adjustment_factor": str(
                        calculation.adjustment_factor
                    ),
                    "integrity_hash": integrity.hash_value,
                },
            )
        )

        result = RewardExecutionResult(
            operation_id=request.operation_id,
            user_id=request.user_id,
            status=uvi_result.status,
            base_reward=calculation.base_reward,
            adjusted_reward=calculation.adjusted_reward,
            reference_price=calculation.reference_price,
            current_price=calculation.current_price,
            adjustment_factor=calculation.adjustment_factor,
            reward_unit=calculation.reward_unit,
            valuation_asset=calculation.valuation_asset,
            quote_asset=calculation.quote_asset,
            uvi_transaction_id=uvi_result.metadata["transaction_id"],
            integrity_hash=integrity.hash_value,
            idempotent=False,
            metadata={
                **dict(calculation.metadata),
                "valuation_verified": True,
                "integrity_verified": False,
            },
        )

        self._idempotency_store.save(
            request.operation_id,
            IdempotencyRecord(
                operation_id=request.operation_id,
                operation_type="REWARD",
                result={
                    "operation_id": result.operation_id,
                    "user_id": result.user_id,
                    "status": result.status,
                    "base_reward": str(result.base_reward),
                    "adjusted_reward": str(result.adjusted_reward),
                    "reference_price": str(result.reference_price),
                    "current_price": str(result.current_price),
                    "adjustment_factor": str(
                        result.adjustment_factor
                    ),
                    "reward_unit": result.reward_unit,
                    "valuation_asset": result.valuation_asset,
                    "quote_asset": result.quote_asset,
                    "uvi_transaction_id": result.uvi_transaction_id,
                    "integrity_hash": result.integrity_hash,
                    "metadata": dict(result.metadata),
                },
            ),
        )

        return result
