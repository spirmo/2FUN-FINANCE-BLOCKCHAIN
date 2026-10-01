"""Financial payment execution through the existing transfer path."""

from financial_core.contracts.payment import PaymentRequest
from financial_core.contracts.payment_execution import PaymentExecutionResult
from financial_core.contracts.transfer import TransferRequest
from financial_core.contracts.idempotency import GenericIdempotencyStore
from financial_core.operations.payment_validator import PaymentValidator
from financial_core.operations.transfer_executor import TransferExecutor
from platform_core.universal_value.ledger.value_ledger import ValueLedger


class PaymentExecutor:
    """
    Execute payments by delegating value movement to the existing
    TransferExecutor.

    Payment does not own a separate ledger or balance authority.
    Persistent idempotency is delegated to the existing generic
    idempotency boundary through TransferExecutor.
    """

    def __init__(
        self,
        ledger: ValueLedger,
        transfer_executor: TransferExecutor | None = None,
        idempotency_store: GenericIdempotencyStore | None = None,
    ):
        self._validator = PaymentValidator()

        if transfer_executor is not None:
            self._transfer_executor = transfer_executor
        else:
            self._transfer_executor = TransferExecutor(
                ledger,
                idempotency_store=idempotency_store,
            )

    def execute(
        self,
        request: PaymentRequest,
    ) -> PaymentExecutionResult:
        """Validate and execute one payment through TransferExecutor."""

        validation = self._validator.validate(request)

        if not validation.valid:
            raise ValueError(validation.reason)

        transfer_request = TransferRequest(
            operation_id=request.operation_id,
            source_account_id=request.payer_account_id,
            destination_account_id=request.payee_account_id,
            amount=request.amount,
            unit=request.unit,
            metadata={
                **dict(request.metadata),
                "operation_type": "PAYMENT",
                "payment_id": request.operation_id,
            },
        )

        transfer_result = self._transfer_executor.execute(
            transfer_request
        )

        return PaymentExecutionResult(
            operation_id=request.operation_id,
            payment_id=request.operation_id,
            payer_account_id=request.payer_account_id,
            payee_account_id=request.payee_account_id,
            amount=request.amount,
            unit=request.unit,
            status=transfer_result.status,
            transfer_operation_id=transfer_result.operation_id,
            payer_uvi_transaction_id=(
                transfer_result.source_uvi_transaction_id
            ),
            payee_uvi_transaction_id=(
                transfer_result.destination_uvi_transaction_id
            ),
            financial_transaction_hash=(
                transfer_result.financial_transaction_hash
            ),
            metadata={
                **dict(transfer_result.metadata or {}),
                "payment_execution": "TRANSFER_BACKED",
                "authority": "EXISTING_UVI",
                "idempotency": "GENERIC_PERSISTENT",
            },
        )
