"""Exchange conversion adapter for the existing 2FUN-OS UVI."""

from decimal import Decimal

from financial_core.contracts.uvi import (
    UVIValueRequest,
    UVIValueResult,
)
from platform_core.universal_value.converters.conversion_engine import (
    ConversionEngine,
)
from platform_core.universal_value.core.contracts import ValueEvent
from platform_core.universal_value.ledger.value_ledger import ValueLedger
from platform_core.universal_value.transactions.transaction_manager import (
    TransactionManager,
)


class UVIExchangeAdapter:
    """Execute an Exchange conversion through the existing UVI."""

    def __init__(self, ledger: ValueLedger):
        self._ledger = ledger
        self._transaction_manager = TransactionManager(ledger)
        self._conversion_engine = ConversionEngine()

    def process(
        self,
        request: UVIValueRequest,
        *,
        target_unit: str,
        quoted_target_amount: str,
        conversion_rate: str,
    ) -> UVIValueResult:
        """Validate, calculate, and record an exchange conversion in UVI."""

        amount = Decimal(request.amount)
        rate = Decimal(conversion_rate)
        quoted_target = Decimal(quoted_target_amount)

        if self._ledger.balance(request.user_id, request.unit) < amount:
            raise ValueError("insufficient UVI balance")

        conversion = self._conversion_engine.convert(
            amount=amount,
            source_currency=request.unit,
            target_currency=target_unit,
            rate=rate,
        )

        if conversion.target_amount != quoted_target:
            raise ValueError(
                "quoted target amount does not match UVI conversion result"
            )

        source_event = ValueEvent(
            event_id=f"{request.operation_id}:OUT",
            user_id=request.user_id,
            source="EXCHANGE",
            action="CONVERSION_OUT",
            base_value=conversion.source_amount,
            currency=request.unit,
            metadata=dict(request.metadata),
        )

        source_transaction = self._transaction_manager.create_transaction(
            event=source_event,
            amount=conversion.source_amount,
            transaction_type="CONVERSION_OUT",
            metadata={
                **dict(request.metadata),
                "financial_core_operation_id": request.operation_id,
                "conversion_reference": request.operation_id,
                "conversion_side": "SOURCE",
                "target_unit": target_unit,
            },
        )

        target_event = ValueEvent(
            event_id=f"{request.operation_id}:IN",
            user_id=request.user_id,
            source="EXCHANGE",
            action="CONVERSION_IN",
            base_value=conversion.target_amount,
            currency=target_unit,
            metadata=dict(request.metadata),
        )

        target_transaction = self._transaction_manager.create_transaction(
            event=target_event,
            amount=conversion.target_amount,
            transaction_type="CONVERSION_IN",
            metadata={
                **dict(request.metadata),
                "financial_core_operation_id": request.operation_id,
                "conversion_reference": request.operation_id,
                "conversion_side": "TARGET",
                "source_unit": request.unit,
            },
        )

        return UVIValueResult(
            operation_id=request.operation_id,
            status="RECORDED",
            recorded=True,
            metadata={
                "authority": "EXISTING_UVI",
                "source_transaction_id": source_transaction.transaction_id,
                "target_transaction_id": target_transaction.transaction_id,
                "source_unit": request.unit,
                "target_unit": target_unit,
                "source_amount": str(conversion.source_amount),
                "target_amount": str(conversion.target_amount),
                "rate": str(conversion.rate),
                "remainder": str(conversion.remainder),
            },
        )
