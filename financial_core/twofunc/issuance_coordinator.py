"""Coordinate persistent 2FUNC issuance and release-state recording.

This coordinator is not an authoritative on-chain issuer. It connects the
local persistent native ledger to the separate release-state database and
supports recovery when the process stops between those two writes.
"""

from datetime import date

from financial_core.interfaces.native_ledger import (
    DuplicateTransaction,
    Issuance,
    LedgerError,
    NativeLedgerPort,
)
from financial_core.twofunc.release_schedule import (
    TwoFuncReleaseSchedule,
)
from financial_core.twofunc.release_state import (
    ReleaseStateError,
    TwoFuncReleaseState,
)
from financial_core.twofunc.supply import (
    BASE_UNITS_PER_2FUNC,
)


class IssuanceCoordinatorError(RuntimeError):
    """Raised when ledger and release-state records cannot be reconciled."""


class TwoFuncIssuanceCoordinator:
    """Coordinate issuance across the ledger and release-state databases.

    The ledger is written first. If recording release state subsequently
    fails, retrying the same request reconciles the existing ledger issuance
    instead of issuing the coins again.
    """

    def __init__(
        self,
        ledger: NativeLedgerPort,
        release_state: TwoFuncReleaseState,
        schedule: TwoFuncReleaseSchedule,
    ):
        if not isinstance(release_state, TwoFuncReleaseState):
            raise IssuanceCoordinatorError(
                "release_state must be a TwoFuncReleaseState"
            )
        if not isinstance(schedule, TwoFuncReleaseSchedule):
            raise IssuanceCoordinatorError(
                "schedule must be a TwoFuncReleaseSchedule"
            )
        if not callable(getattr(ledger, "issue_to", None)):
            raise IssuanceCoordinatorError(
                "ledger must provide issue_to()"
            )
        if not callable(getattr(ledger, "issuance_for", None)):
            raise IssuanceCoordinatorError(
                "ledger must provide issuance_for()"
            )
        if not callable(getattr(ledger, "transaction_exists", None)):
            raise IssuanceCoordinatorError(
                "ledger must provide transaction_exists()"
            )

        self._ledger = ledger
        self._release_state = release_state
        self._schedule = schedule

    def _validate_release_capacity(
        self,
        *,
        stage_number: int,
        amount: int,
        recorded_on: date,
    ) -> None:
        stage = self._schedule.stage(stage_number)
        snapshot = self._release_state.snapshot()
        state = snapshot[stage_number]
        started_on = state["started_on"]

        if started_on is None:
            raise ReleaseStateError(
                "cannot issue coins for an inactive release stage"
            )

        if date.fromisoformat(started_on) > recorded_on:
            raise ReleaseStateError(
                "issuance date cannot precede stage activation"
            )

        allocation = stage.amount * BASE_UNITS_PER_2FUNC
        already_recorded = int(state["issued_amount"])

        if amount > allocation - already_recorded:
            raise ReleaseStateError(
                "issuance would exceed this stage's remaining allocation"
            )

    def issue(
        self,
        *,
        tx_id: str,
        recipient: str,
        stage_number: int,
        amount: int,
        recorded_on: date,
    ) -> Issuance:
        """Issue once and record release state; retry safely after interruption.

        Amount is an integer number of native base units, not whole 2FUNC.
        """
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise IssuanceCoordinatorError(
                "transaction ID is required"
            )
        if not isinstance(recipient, str) or not recipient.strip():
            raise IssuanceCoordinatorError(
                "recipient is required"
            )
        if isinstance(stage_number, bool) or not isinstance(stage_number, int):
            raise IssuanceCoordinatorError(
                "stage number must be an integer"
            )
        if not 1 <= stage_number <= 10:
            raise IssuanceCoordinatorError(
                "stage number must be between 1 and 10"
            )
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise IssuanceCoordinatorError(
                "amount must be a positive integer base-unit amount"
            )
        if not isinstance(recorded_on, date):
            raise IssuanceCoordinatorError(
                "recorded_on must be a date"
            )

        # Validate the stage number against the supplied schedule.
        self._schedule.stage(stage_number)

        ledger_record = self._ledger.issuance_for(tx_id)
        state_record = self._release_state.issuance_record(tx_id)

        if ledger_record is None:
            if state_record is not None:
                raise IssuanceCoordinatorError(
                    "release state has an issuance record absent from the ledger"
                )

            if self._ledger.transaction_exists(tx_id):
                raise DuplicateTransaction(
                    "transaction ID is already used by a non-issuance transaction"
                )

            # Preflight before touching the ledger. The release-state write
            # still validates its own invariants after the ledger write.
            self._validate_release_capacity(
                stage_number=stage_number,
                amount=amount,
                recorded_on=recorded_on,
            )

            ledger_record = self._ledger.issue_to(
                tx_id,
                recipient,
                amount,
            )

        # Whether this is a new issuance or a retry, the ledger record must
        # exactly match the requested operation.
        if (
            ledger_record.tx_id != tx_id
            or ledger_record.recipient != recipient
            or ledger_record.amount != amount
        ):
            raise IssuanceCoordinatorError(
                "existing ledger issuance does not match the request"
            )

        if state_record is not None:
            if (
                state_record["stage_number"] != stage_number
                or state_record["amount"] != amount
            ):
                raise IssuanceCoordinatorError(
                    "existing release record does not match the request"
                )
            return ledger_record

        # If the process previously stopped after the ledger commit, this
        # records the existing issuance without minting a second time.
        self._release_state.record_issuance(
            self._schedule,
            tx_id=tx_id,
            stage_number=stage_number,
            amount=amount,
            recorded_on=recorded_on,
        )
        return ledger_record
