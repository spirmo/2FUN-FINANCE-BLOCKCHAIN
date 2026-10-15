"""Blockchain settlement gateway implementation."""

import hashlib

from financial_core.blockchain.adapter import BlockchainNetworkAdapter
from financial_core.blockchain.contracts import BlockchainSubmissionRequest
from financial_core.contracts.transaction_hash import TransactionIdentity
from financial_core.settlement.contracts import (
    SettlementRecord,
    SettlementRequest,
)
from financial_core.settlement.gateway import BlockchainGateway


class BlockchainSettlementGateway(BlockchainGateway):
    """Settlement boundary for pending or adapter-backed blockchain submission."""

    def __init__(
        self,
        network_adapter: BlockchainNetworkAdapter | None = None,
    ) -> None:
        self._network_adapter = network_adapter

    def settle(self, request: SettlementRequest) -> SettlementRecord:
        if self._network_adapter is not None:
            submission = self._network_adapter.submit(
                BlockchainSubmissionRequest(
                    operation_id=request.operation_id,
                    amount=request.amount,
                    unit=request.unit,
                    metadata=dict(request.metadata),
                )
            )

            if submission.operation_id != request.operation_id:
                raise ValueError(
                    "blockchain adapter returned a mismatched operation_id"
                )

            # An adapter-reported status is not proof of network finality.
            # Until authenticated network evidence is implemented, downgrade
            # confirmation claims to SUBMITTED and preserve the reported
            # status separately for diagnostics.
            reported_status = str(submission.status).upper()
            if reported_status not in {
                "SUBMITTED",
                "PENDING_SUBMISSION",
                "CONFIRMING",
                "CONFIRMED",
                "FINALIZED",
                "FAILED",
                "REORGED",
            }:
                raise ValueError(
                    f"unsupported blockchain adapter status: {submission.status}"
                )

            if reported_status in {"CONFIRMED", "FINALIZED"}:
                effective_status = "SUBMITTED"
            else:
                effective_status = reported_status

            identity = TransactionIdentity(
                operation_id=request.operation_id,
                uvi_transaction_id=str(
                    request.metadata.get("uvi_transaction_id", "")
                ),
                financial_transaction_hash=request.metadata.get(
                    "financial_transaction_hash"
                ),
                blockchain_tx_hash=submission.blockchain_tx_hash,
            )
            metadata = {
                **dict(request.metadata),
                **dict(submission.metadata),
                "settlement_mode": "ON_CHAIN",
                "blockchain_status": effective_status,
                "adapter_reported_status": reported_status,
                "transaction_identity": identity,
                "blockchain_tx_hash": submission.blockchain_tx_hash,
            }

            return SettlementRecord(
                operation_id=request.operation_id,
                settlement_type=request.settlement_type,
                amount=request.amount,
                unit=request.unit,
                status=effective_status,
                transaction_reference=(
                    submission.blockchain_tx_hash
                    or f"bc-submit-{request.operation_id}"
                ),
                metadata=metadata,
            )

        payload = (
            f"{request.operation_id}|"
            f"{request.settlement_type}|"
            f"{request.amount}|"
            f"{request.unit}"
        )
        submission_reference = (
            "bc-submit-"
            + hashlib.sha256(payload.encode("utf-8")).hexdigest()
        )
        identity = TransactionIdentity(
            operation_id=request.operation_id,
            uvi_transaction_id=str(
                request.metadata.get("uvi_transaction_id", "")
            ),
            financial_transaction_hash=request.metadata.get(
                "financial_transaction_hash"
            ),
            blockchain_tx_hash=None,
        )
        metadata = {
            **dict(request.metadata),
            "settlement_mode": "ON_CHAIN",
            "blockchain_status": "PENDING_SUBMISSION",
            "submission_reference": submission_reference,
            "transaction_identity": identity,
            "blockchain_tx_hash": None,
        }

        return SettlementRecord(
            operation_id=request.operation_id,
            settlement_type=request.settlement_type,
            amount=request.amount,
            unit=request.unit,
            status="SUBMITTED",
            transaction_reference=submission_reference,
            metadata=metadata,
        )
