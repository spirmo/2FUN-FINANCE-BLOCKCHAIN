"""Persistent SQLite state for the 10-stage native 2FUNC release process."""

import calendar
import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path

from financial_core.twofunc.release_schedule import (
    ReleaseScheduleError,
    TwoFuncReleaseSchedule,
    STAGE_COUNT,
)
from financial_core.twofunc.supply import MAX_SUPPLY_BASE_UNITS, BASE_UNITS_PER_2FUNC


MIN_ISSUED_PERCENT = 90
MIN_INTERVAL_MONTHS = 6


class ReleaseStateError(ValueError):
    """Raised when persistent release state violates its invariants."""


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise ReleaseStateError("date must use ISO format YYYY-MM-DD") from exc


def _add_calendar_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year, month_zero = divmod(month_index, 12)
    month = month_zero + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


class TwoFuncReleaseState:
    """Persist stage activation and issued amounts in a SQLite database.

    This repository records release state; it does not mint coins and is not
    itself an authoritative on-chain ledger. Issuance must be reconciled with
    the authoritative ledger before this state is used for production release.
    """

    def __init__(self, database_path: str | Path):
        """Connect to an existing database with the official release schema.

        This class never creates a database, tables, or stage records.
        Schema creation belongs to the 2FUN-OS database migration.
        """
        if not isinstance(database_path, (str, Path)):
            raise ReleaseStateError("an explicit database path is required")

        self.database_path = str(database_path)

        if self.database_path != ":memory:":
            database_file = Path(self.database_path).expanduser()
            if not database_file.is_file():
                raise ReleaseStateError(
                    f"release database does not exist: {database_file}"
                )
            self.database_path = str(database_file)

        try:
            with self._connection() as connection:
                expected = {
                    "release_stage_state": {
                        "stage_number": "INTEGER",
                        "started_on": "TEXT",
                        "issued_amount": "TEXT",
                    },
                    "release_issuance_records": {
                        "tx_id": "TEXT",
                        "stage_number": "INTEGER",
                        "amount": "TEXT",
                        "recorded_at": "TEXT",
                    },
                }

                for table, expected_columns in expected.items():
                    rows = connection.execute(
                        f"PRAGMA table_info({table})"
                    ).fetchall()

                    if not rows:
                        raise ReleaseStateError(
                            f"required table is missing: {table}"
                        )

                    actual_columns = {
                        row["name"]: row["type"].upper()
                        for row in rows
                    }

                    for column, expected_type in expected_columns.items():
                        actual_type = actual_columns.get(column)
                        if actual_type != expected_type:
                            raise ReleaseStateError(
                                f"incompatible schema: {table}.{column}; "
                                f"expected {expected_type}, found {actual_type}"
                            )

                stages = connection.execute(
                    """
                    SELECT stage_number
                    FROM release_stage_state
                    ORDER BY stage_number
                    """
                ).fetchall()

                stage_numbers = [row["stage_number"] for row in stages]
                expected_numbers = list(range(1, STAGE_COUNT + 1))

                if stage_numbers != expected_numbers:
                    raise ReleaseStateError(
                        "release database must contain exactly stages 1 through 10"
                    )

        except sqlite3.Error as exc:
            raise ReleaseStateError(
                f"cannot validate release database: {exc}"
            ) from exc

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=10)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def _connection(self):
        """Manage transaction completion and always close the connection."""
        connection = self._connect()
        try:
            yield connection
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()

    def snapshot(self) -> dict[int, dict[str, int | str | None]]:
        """Return persisted activation dates and cumulative issued amounts."""
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT stage_number, started_on, issued_amount
                FROM release_stage_state
                ORDER BY stage_number
                """
            ).fetchall()

        return {
            row["stage_number"]: {
                "started_on": row["started_on"],
                "issued_amount": row["issued_amount"],
            }
            for row in rows
        }

    def active_stage_number(self) -> int | None:
        """Return the highest activated stage, or None if none has started."""
        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT MAX(stage_number) AS active_number
                FROM release_stage_state
                WHERE started_on IS NOT NULL
                """
            ).fetchone()
        return row["active_number"]

    def activate_first_stage(self, started_on: date) -> None:
        """Record the actual activation date of stage 1 exactly once."""
        if not isinstance(started_on, date) or isinstance(started_on, datetime):
            raise ReleaseStateError("started_on must be a date")

        with self._connection() as connection:
            row = connection.execute(
                "SELECT started_on FROM release_stage_state WHERE stage_number = 1"
            ).fetchone()
            if row["started_on"] is not None:
                raise ReleaseStateError("stage 1 has already been activated")

            connection.execute(
                """
                UPDATE release_stage_state
                SET started_on = ?
                WHERE stage_number = 1 AND started_on IS NULL
                """,
                (started_on.isoformat(),),
            )

    def next_stage_eligible(
        self,
        schedule: TwoFuncReleaseSchedule,
        as_of: date,
    ) -> int | None:
        """Return the next stage number only when both activation gates pass."""
        if not isinstance(schedule, TwoFuncReleaseSchedule):
            raise ReleaseStateError("schedule must be a TwoFuncReleaseSchedule")
        if not isinstance(as_of, date) or isinstance(as_of, datetime):
            raise ReleaseStateError("as_of must be a date")

        active = self.active_stage_number()
        if active is None or active >= STAGE_COUNT:
            return None

        state = self.snapshot()
        previous = state[active]
        started_on = previous["started_on"]
        if started_on is None:
            return None

        actual_start = _parse_date(started_on)
        if actual_start > as_of:
            return None

        allocation = schedule.stage(active).amount * BASE_UNITS_PER_2FUNC
        issued = int(previous["issued_amount"])
        if issued * 100 < allocation * MIN_ISSUED_PERCENT:
            return None

        if as_of < _add_calendar_months(actual_start, MIN_INTERVAL_MONTHS):
            return None

        return active + 1

    def activate_next_stage(
        self,
        schedule: TwoFuncReleaseSchedule,
        started_on: date,
    ) -> int:
        """Activate the next stage after validating both gates, atomically."""
        if not isinstance(started_on, date) or isinstance(started_on, datetime):
            raise ReleaseStateError("started_on must be a date")

        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT stage_number, started_on, issued_amount
                FROM release_stage_state
                ORDER BY stage_number
                """
            ).fetchall()
            active_rows = [row for row in rows if row["started_on"] is not None]
            if not active_rows:
                raise ReleaseStateError("stage 1 must be activated first")

            previous = active_rows[-1]
            active = previous["stage_number"]
            if active >= STAGE_COUNT:
                raise ReleaseStateError("all release stages are already activated")

            actual_start = _parse_date(previous["started_on"])
            if started_on < actual_start:
                raise ReleaseStateError("activation date cannot precede the previous stage")

            allocation = schedule.stage(active).amount * BASE_UNITS_PER_2FUNC
            issued = int(previous["issued_amount"])
            if issued * 100 < allocation * MIN_ISSUED_PERCENT:
                raise ReleaseStateError(
                    "next stage requires at least 90% issuance of the previous allocation"
                )

            if started_on < _add_calendar_months(actual_start, MIN_INTERVAL_MONTHS):
                raise ReleaseStateError(
                    "at least six calendar months must elapse between actual stage starts"
                )

            next_number = active + 1
            connection.execute(
                """
                UPDATE release_stage_state
                SET started_on = ?
                WHERE stage_number = ? AND started_on IS NULL
                """,
                (started_on.isoformat(), next_number),
            )
            if connection.total_changes != 1:
                raise ReleaseStateError("next stage is already activated")

        return next_number

    def record_issuance(
        self,
        schedule: TwoFuncReleaseSchedule,
        *,
        tx_id: str,
        stage_number: int,
        amount: int,
        recorded_on: date,
    ) -> None:
        """Record an externally confirmed issuance; this method never mints."""
        if not isinstance(schedule, TwoFuncReleaseSchedule):
            raise ReleaseStateError("schedule must be a TwoFuncReleaseSchedule")
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ReleaseStateError("transaction ID is required")
        if isinstance(stage_number, bool) or not isinstance(stage_number, int):
            raise ReleaseStateError("stage number must be an integer")
        if not 1 <= stage_number <= STAGE_COUNT:
            raise ReleaseStateError("stage number must be between 1 and 10")
        if isinstance(amount, bool) or not isinstance(amount, int) or amount <= 0:
            raise ReleaseStateError("amount must be a positive integer base-unit amount")
        if not isinstance(recorded_on, date) or isinstance(recorded_on, datetime):
            raise ReleaseStateError("recorded_on must be a date")

        allocation = schedule.stage(stage_number).amount * BASE_UNITS_PER_2FUNC
        with self._connection() as connection:
            stage = connection.execute(
                """
                SELECT started_on, issued_amount
                FROM release_stage_state WHERE stage_number = ?
                """,
                (stage_number,),
            ).fetchone()

            if stage["started_on"] is None:
                raise ReleaseStateError("cannot record issuance for an inactive stage")
            if _parse_date(stage["started_on"]) > recorded_on:
                raise ReleaseStateError("issuance date cannot precede stage activation")
            if amount > allocation - int(stage["issued_amount"]):
                raise ReleaseStateError("issuance would exceed this stage's allocation")

            try:
                connection.execute(
                    """
                    INSERT INTO release_issuance_records
                        (tx_id, stage_number, amount, recorded_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        tx_id,
                        stage_number,
                        str(amount),
                        datetime.now(timezone.utc).isoformat(),
                    ),
                )
            except sqlite3.IntegrityError as exc:
                raise ReleaseStateError(
                    "duplicate issuance transaction ID or invalid issuance record"
                ) from exc

            new_stage_total = int(stage["issued_amount"]) + amount
            connection.execute(
                """
                UPDATE release_stage_state
                SET issued_amount = ?
                WHERE stage_number = ?
                """,
                (str(new_stage_total), stage_number),
            )

            rows = connection.execute(
                "SELECT issued_amount FROM release_stage_state"
            ).fetchall()
            total_issued = sum(int(row["issued_amount"]) for row in rows)
            if total_issued > MAX_SUPPLY_BASE_UNITS:
                raise ReleaseStateError("recorded issuance exceeds the global supply cap")

    def issuance_record(self, tx_id: str) -> dict | None:
        """Return a persisted issuance record by transaction ID."""
        if not isinstance(tx_id, str) or not tx_id.strip():
            raise ReleaseStateError("transaction ID is required")

        with self._connection() as connection:
            row = connection.execute(
                """
                SELECT tx_id, stage_number, amount, recorded_at
                FROM release_issuance_records
                WHERE tx_id = ?
                """,
                (tx_id,),
            ).fetchone()

        if row is None:
            return None

        return {
            "tx_id": row["tx_id"],
            "stage_number": int(row["stage_number"]),
            "amount": int(row["amount"]),
            "recorded_at": row["recorded_at"],
        }

    def issuance_total(self) -> int:
        """Return cumulative amounts recorded here in native base units."""
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT issued_amount FROM release_stage_state"
            ).fetchall()
            return sum(int(row["issued_amount"]) for row in rows)
