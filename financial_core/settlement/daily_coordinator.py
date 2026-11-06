"""Persistent coordinator for daily 2FUNC settlement scheduling.

This module records settlement destination choices and settlement intents.
It does not move funds or claim that a value transfer has completed.
All operational timestamps use UTC.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, time, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Callable, Iterator
from uuid import uuid4


ALLOWED_DESTINATIONS = frozenset({"Drika", "SHIR", "ΣSHIR", "2FUNC", "Drik"})
DEFAULT_DESTINATION = "Drika"
SELECTION_START = time(22, 30)
SELECTION_END = time(23, 30)


class DailySettlementError(Exception):
    """Base error for daily settlement coordination."""


class SelectionWindowClosed(DailySettlementError):
    """Raised when a destination is selected outside the allowed window."""


class SettlementAlreadyFinalized(DailySettlementError):
    """Raised when the operational day already has a final settlement intent."""


class DailySettlementCoordinator:
    """Coordinate daily settlement using the host ecosystem database."""

    def __init__(
        self,
        connection_factory: Callable[[], sqlite3.Connection],
    ):
        if not callable(connection_factory):
            raise TypeError(
                "connection_factory must provide connections "
                "to the ecosystem database."
            )
        self.connection_factory = connection_factory

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = self.connection_factory()
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA busy_timeout = 30000")
            yield connection
        finally:
            connection.close()

    @staticmethod
    def _utc_now(now: datetime | None = None) -> datetime:
        value = now or datetime.now(timezone.utc)
        if value.tzinfo is None:
            raise ValueError("now must be timezone-aware")
        return value.astimezone(timezone.utc)

    @classmethod
    def _operational_date(cls, now: datetime | None = None) -> date:
        return cls._utc_now(now).date()

    @staticmethod
    def _validate_destination(destination: str) -> str:
        if destination not in ALLOWED_DESTINATIONS:
            raise ValueError(
                f"Unsupported destination: {destination!r}"
            )
        return destination

    def select_destination(
        self,
        *,
        user_id: str,
        destination: str,
        now: datetime | None = None,
    ) -> dict:
        """Persist a user's destination during 22:30–23:30 UTC.

        The interval is start-inclusive and end-exclusive.
        A user's choice can be updated while the window remains open,
        but not after a settlement intent has been created.
        """
        if not user_id:
            raise ValueError("user_id is required")

        destination = self._validate_destination(destination)
        timestamp = self._utc_now(now)

        if not (SELECTION_START <= timestamp.time() < SELECTION_END):
            raise SelectionWindowClosed(
                "Destination selection is open from 22:30 inclusive "
                "until 23:30 exclusive UTC."
            )

        operational_date = timestamp.date().isoformat()
        selected_at = timestamp.isoformat()

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                existing_intent = connection.execute(
                    """
                    SELECT settlement_id
                    FROM daily_settlement_intents
                    WHERE user_id = ? AND operational_date = ?
                    """,
                    (user_id, operational_date),
                ).fetchone()

                if existing_intent is not None:
                    raise SettlementAlreadyFinalized(
                        "A settlement intent already exists for this day."
                    )

                connection.execute(
                    """
                    INSERT INTO daily_settlement_choices (
                        user_id, operational_date, destination,
                        selected_at_utc
                    )
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(user_id, operational_date)
                    DO UPDATE SET
                        destination = excluded.destination,
                        selected_at_utc = excluded.selected_at_utc
                    """,
                    (
                        user_id,
                        operational_date,
                        destination,
                        selected_at,
                    ),
                )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

        return {
            "user_id": user_id,
            "operational_date": operational_date,
            "destination": destination,
            "selected_at_utc": selected_at,
        }

    def get_choice(
        self,
        *,
        user_id: str,
        operational_date: date,
    ) -> dict | None:
        """Return a persisted destination choice, if present."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT user_id, operational_date, destination,
                       selected_at_utc
                FROM daily_settlement_choices
                WHERE user_id = ? AND operational_date = ?
                """,
                (user_id, operational_date.isoformat()),
            ).fetchone()

        return dict(row) if row is not None else None

    def create_settlement_intent(
        self,
        *,
        user_id: str,
        operational_date: date,
        now: datetime | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Create one durable intent at or after 00:00 UTC.

        The intent is NOT a completed transfer. A separate, reliable
        settlement backend must perform and confirm the actual movement.
        """
        if not user_id:
            raise ValueError("user_id is required")

        timestamp = self._utc_now(now)
        day = operational_date.isoformat()

        if timestamp.date() < operational_date:
            raise ValueError("Cannot settle a future operational date")

        if timestamp.date() == operational_date:
            raise ValueError(
                "Daily settlement intent is created from 00:00 UTC "
                "on the following operational day."
            )

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                existing = connection.execute(
                    """
                    SELECT *
                    FROM daily_settlement_intents
                    WHERE user_id = ? AND operational_date = ?
                    """,
                    (user_id, day),
                ).fetchone()

                if existing is not None:
                    connection.execute("COMMIT")
                    result = dict(existing)
                    result["metadata"] = json.loads(
                        result.pop("metadata_json")
                    )
                    return result

                choice = connection.execute(
                    """
                    SELECT destination
                    FROM daily_settlement_choices
                    WHERE user_id = ? AND operational_date = ?
                    """,
                    (user_id, day),
                ).fetchone()

                destination = (
                    choice["destination"]
                    if choice is not None
                    else DEFAULT_DESTINATION
                )

                settlement_id = str(uuid4())
                operation_id = f"DAILY-SETTLEMENT:{user_id}:{day}"
                created_at = timestamp.isoformat()
                serialized_metadata = json.dumps(
                    metadata or {},
                    ensure_ascii=False,
                    sort_keys=True,
                )

                connection.execute(
                    """
                    INSERT INTO daily_settlement_intents (
                        settlement_id, user_id, operational_date,
                        destination, status, trigger_reason, operation_id,
                        created_at_utc, metadata_json
                    )
                    VALUES (?, ?, ?, ?, 'PENDING', ?, ?, ?, ?)
                    """,
                    (
                        settlement_id,
                        user_id,
                        day,
                        destination,
                        "USER_SELECTED" if choice is not None else "AUTO_DRIKA",
                        operation_id,
                        created_at,
                        serialized_metadata,
                    ),
                )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

        return self.get_intent(
            user_id=user_id,
            operational_date=operational_date,
        )

    def get_intent(
        self,
        *,
        user_id: str,
        operational_date: date,
    ) -> dict | None:
        """Read the durable intent for a user and operational day."""
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM daily_settlement_intents
                WHERE user_id = ? AND operational_date = ?
                """,
                (user_id, operational_date.isoformat()),
            ).fetchone()

        if row is None:
            return None

        result = dict(row)
        result["metadata"] = json.loads(result.pop("metadata_json"))
        return result

    def mark_transfer_completed(
        self,
        *,
        user_id: str,
        operational_date: date,
        source_amount: Decimal,
        source_unit: str,
        destination_amount: Decimal,
        reference_price: Decimal | None = None,
        current_price: Decimal | None = None,
        uvi_transaction_id: str,
        now: datetime | None = None,
    ) -> dict:
        """Record externally confirmed transfer details.

        This method only records confirmation supplied by a trusted caller.
        It does not itself execute or verify the transfer.
        """
        if not uvi_transaction_id:
            raise ValueError("uvi_transaction_id is required")
        if not source_unit:
            raise ValueError("source_unit is required")

        try:
            source = Decimal(str(source_amount))
            destination = Decimal(str(destination_amount))
            reference = (
                None if reference_price is None
                else Decimal(str(reference_price))
            )
            current = (
                None if current_price is None
                else Decimal(str(current_price))
            )
        except (InvalidOperation, ValueError) as exc:
            raise ValueError("Amounts and prices must be valid decimals") from exc

        if not source.is_finite() or not destination.is_finite():
            raise ValueError("Amounts must be finite")
        if source < 0 or destination < 0:
            raise ValueError("Amounts cannot be negative")

        for name, price in (
            ("reference_price", reference),
            ("current_price", current),
        ):
            if price is not None and (
                not price.is_finite() or price <= 0
            ):
                raise ValueError(f"{name} must be finite and positive")

        timestamp = self._utc_now(now)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            try:
                row = connection.execute(
                    """
                    SELECT status, uvi_transaction_id, source_amount, source_unit,
                           destination_amount, reference_price, current_price
                    FROM daily_settlement_intents
                    WHERE user_id = ? AND operational_date = ?
                    """,
                    (user_id, operational_date.isoformat()),
                ).fetchone()

                if row is None:
                    raise DailySettlementError(
                        "No settlement intent exists for this day."
                    )

                if row["status"] == "COMPLETED":
                    same_completion = (
                        row["uvi_transaction_id"] == uvi_transaction_id
                        and Decimal(str(row["source_amount"])) == source
                        and row["source_unit"] == source_unit
                        and Decimal(str(row["destination_amount"])) == destination
                        and (
                            None if row["reference_price"] is None
                            else Decimal(str(row["reference_price"]))
                        ) == reference
                        and (
                            None if row["current_price"] is None
                            else Decimal(str(row["current_price"]))
                        ) == current
                    )
                    if same_completion:
                        connection.execute("COMMIT")
                        return self.get_intent(
                            user_id=user_id,
                            operational_date=operational_date,
                        )
                    raise SettlementAlreadyFinalized(
                        "Settlement was already completed with conflicting details."
                    )

                if row["status"] != "PENDING":
                    raise DailySettlementError(
                        "Cannot complete settlement in status " + repr(row["status"]) + "."
                    )

                connection.execute(
                    """
                    UPDATE daily_settlement_intents
                    SET status = 'COMPLETED',
                        finalized_at_utc = ?,
                        source_amount = ?,
                        source_unit = ?,
                        destination_amount = ?,
                        reference_price = ?,
                        current_price = ?,
                        uvi_transaction_id = ?
                    WHERE user_id = ? AND operational_date = ?
                    """,
                    (
                        timestamp.isoformat(),
                        str(source),
                        source_unit,
                        str(destination),
                        None if reference is None else str(reference),
                        None if current is None else str(current),
                        uvi_transaction_id,
                        user_id,
                        operational_date.isoformat(),
                    ),
                )
                connection.execute("COMMIT")
            except Exception:
                connection.execute("ROLLBACK")
                raise

        return self.get_intent(
            user_id=user_id,
            operational_date=operational_date,
        )
