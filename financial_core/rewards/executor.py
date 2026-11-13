"""End-to-end price-adjusted reward executor."""

from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from financial_core.profiles.daily_profile import DailyProfileStore

from financial_core.contracts.idempotency import IdempotencyRecord
from financial_core.contracts.integrity import IntegrityRequest
from financial_core.contracts.reward_execution import (
    RewardExecutionRequest,
    RewardExecutionResult,
)
from financial_core.contracts.uvi import UVIValueRequest
from financial_core.contracts.valuation import ValuationRequest
from financial_core.idempotency.generic_sqlite_store import (
    GenericSQLiteIdempotencyStore,
)
from financial_core.contracts.uvi import UVIAdapter
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
        uvi_adapter: UVIAdapter,
        idempotency_store: GenericSQLiteIdempotencyStore,
        integrity_provider: "UniversalIntegrityAdapter | None" = None,
        profile_store: DailyProfileStore | None = None,
        activity_date_provider=None,
    ):
        self._valuation_provider = valuation_provider
        self._uvi_adapter = uvi_adapter
        self._idempotency_store = idempotency_store
        if integrity_provider is None:
            from financial_core.integrations.integrity_adapter import (
                UniversalIntegrityAdapter,
            )

            integrity_provider = UniversalIntegrityAdapter()

        self._integrity_provider = integrity_provider
        self._calculator = PriceAdjustedRewardCalculator()
        self._profile_store = profile_store
        self._activity_date_provider = activity_date_provider or date.today

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
                adjustment_factor=Decimal(data["adjustment_factor"]),
                reward_unit=data["reward_unit"],
                valuation_asset=data["valuation_asset"],
                quote_asset=data["quote_asset"],
                uvi_transaction_id=data["uvi_transaction_id"],
                integrity_hash=data["integrity_hash"],
                idempotent=True,
                metadata={"integrity_verified": False},
            )

        if request.valuation_asset != "2FUNC":
            raise ValueError("Reward valuation supports only 2FUNC")
        if request.quote_asset != "USD":
            raise ValueError("Reward valuation requires USD as quote asset")
        if self._valuation_provider is None:
            raise ValueError("A verified valuation provider is required")

        valuation_timestamp = datetime.now(timezone.utc).isoformat()
        valuation = self._valuation_provider.get_value(
            ValuationRequest(
                asset=request.valuation_asset,
                quote_asset=request.quote_asset,
                timestamp=valuation_timestamp,
                metadata={"operation_id": request.operation_id},
            )
        )

        if not valuation.verified:
            raise ValueError("Valuation provider returned an unverified result")
        if valuation.asset != request.valuation_asset:
            raise ValueError("Valuation provider returned an unexpected asset")
        if valuation.quote_asset != request.quote_asset:
            raise ValueError("Valuation provider returned an unexpected quote asset")
        if not valuation.source:
            raise ValueError("Valuation provider returned no source")

        try:
            valuation_price = Decimal(valuation.price)
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("Valuation provider returned an invalid price") from exc

        if not valuation_price.is_finite() or valuation_price <= 0:
            raise ValueError("Valuation provider price must be finite and positive")

        # Before listing, the approved base-price policy is also the current
        # valuation. Both calculation inputs therefore come from the provider.
        calculation = self._calculator.calculate(
            request=__import__(
                "financial_core.contracts.reward",
                fromlist=["RewardCalculationRequest"],
            ).RewardCalculationRequest(
                operation_id=request.operation_id,
                base_reward=request.base_reward,
                reference_price=valuation_price,
                current_price=valuation_price,
                reward_unit=request.reward_unit,
                valuation_asset=valuation.asset,
                quote_asset=valuation.quote_asset,
                metadata={
                    **dict(request.metadata or {}),
                    "valuation_source": valuation.source,
                    "valuation_timestamp": valuation.timestamp,
                    "valuation_verified": True,
                    "valuation_metadata": dict(valuation.metadata or {}),
                },
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

        if self._profile_store is not None:
            self._profile_store.record_activity(
                operation_id=request.operation_id,
                user_id=request.user_id,
                activity_date=self._activity_date_provider(),
                base_points=calculation.base_reward,
                value_points=calculation.adjusted_reward,
                reference_price=calculation.reference_price,
                current_price=calculation.current_price,
                reward_unit=calculation.reward_unit,
                uvi_transaction_id=uvi_result.metadata["transaction_id"],
            )

        result = RewardExecutionResult(
            operation_id=request.operation_id,
            user_id=request.user_id,
            status=uvi_result.status,
            base_reward=calculation.base_reward,
            adjusted_reward=calculation.adjusted_reward,
            adjustment_factor=calculation.adjustment_factor,
            reward_unit=calculation.reward_unit,
            valuation_asset=calculation.valuation_asset,
            quote_asset=calculation.quote_asset,
            uvi_transaction_id=uvi_result.metadata["transaction_id"],
            integrity_hash=integrity.hash_value,
            idempotent=False,
            metadata={"integrity_verified": False},
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
