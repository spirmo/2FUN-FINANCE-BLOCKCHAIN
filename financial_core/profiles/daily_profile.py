from contextlib import closing
"""Persistent daily profile for base and price-adjusted reward points."""

import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path


class DailyProfileStore:
    """Persist activity points and provide daily/lifetime summaries.

    This component does not own UVI balances and does not execute settlement.
    Base points are immutable historical activity records.
    """

    def __init__(self, database_path: str | Path):
        self._database_path = str(database_path)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self._database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        with closing(self._connect()) as connection, connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_profile_activities (
                    operation_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    activity_date TEXT NOT NULL,
                    base_points TEXT NOT NULL,
                    value_points TEXT NOT NULL,
                    reference_price TEXT NOT NULL,
                    current_price TEXT NOT NULL,
                    reward_unit TEXT NOT NULL,
                    uvi_transaction_id TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_daily_profile_user_date
                ON daily_profile_activities(user_id, activity_date)
                """
            )

    @staticmethod
    def _decimal_string(value, field_name):
        try:
            number = Decimal(str(value))
        except Exception as exc:
            raise ValueError(f"{field_name} must be a valid decimal") from exc

        if not number.is_finite() or number < 0:
            raise ValueError(f"{field_name} must be finite and non-negative")

        return str(number)

    def record_activity(
        self,
        *,
        operation_id: str,
        user_id: str,
        activity_date: date,
        base_points,
        value_points,
        reference_price,
        current_price,
        reward_unit: str,
        uvi_transaction_id: str,
    ) -> bool:
        """Record an activity once; return False for an identical replay.

        Reusing an operation ID with different data raises ValueError.
        """
        if not operation_id or not user_id or not uvi_transaction_id:
            raise ValueError(
                "operation_id, user_id and uvi_transaction_id are required"
            )
        if not reward_unit:
            raise ValueError("reward_unit is required")
        if not isinstance(activity_date, date):
            raise ValueError("activity_date must be a datetime.date")

        base = self._decimal_string(base_points, "base_points")
        value = self._decimal_string(value_points, "value_points")
        reference = self._decimal_string(reference_price, "reference_price")
        current = self._decimal_string(current_price, "current_price")

        if Decimal(reference) <= 0 or Decimal(current) <= 0:
            raise ValueError("prices must be greater than zero")

        values = (
            operation_id,
            user_id,
            activity_date.isoformat(),
            base,
            value,
            reference,
            current,
            reward_unit,
            uvi_transaction_id,
        )

        with closing(self._connect()) as connection, connection:
            existing = connection.execute(
                """
                SELECT operation_id, user_id, activity_date, base_points,
                       value_points, reference_price, current_price,
                       reward_unit, uvi_transaction_id
                FROM daily_profile_activities
                WHERE operation_id = ?
                """,
                (operation_id,),
            ).fetchone()

            if existing is not None:
                existing_values = tuple(existing[key] for key in (
                    "operation_id",
                    "user_id",
                    "activity_date",
                    "base_points",
                    "value_points",
                    "reference_price",
                    "current_price",
                    "reward_unit",
                    "uvi_transaction_id",
                ))
                if existing_values != values:
                    raise ValueError(
                        "operation_id already exists with different activity data"
                    )
                return False

            connection.execute(
                """
                INSERT INTO daily_profile_activities (
                    operation_id, user_id, activity_date, base_points,
                    value_points, reference_price, current_price,
                    reward_unit, uvi_transaction_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                values,
            )

        return True

    def daily_summary(self, user_id: str, activity_date: date) -> dict:
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS activity_count,
                       COALESCE(SUM(CAST(base_points AS NUMERIC)), 0)
                           AS daily_base_points,
                       COALESCE(SUM(CAST(value_points AS NUMERIC)), 0)
                           AS daily_value_points
                FROM daily_profile_activities
                WHERE user_id = ? AND activity_date = ?
                """,
                (user_id, activity_date.isoformat()),
            ).fetchone()

        return {
            "user_id": user_id,
            "activity_date": activity_date.isoformat(),
            "activity_count": row["activity_count"],
            "daily_base_points": str(row["daily_base_points"]),
            "daily_value_points": str(row["daily_value_points"]),
        }

    def lifetime_base_points(self, user_id: str) -> str:
        """Return cumulative base points; settlement never reduces this value."""
        with closing(self._connect()) as connection, connection:
            row = connection.execute(
                """
                SELECT COALESCE(SUM(CAST(base_points AS NUMERIC)), 0)
                    AS total
                FROM daily_profile_activities
                WHERE user_id = ?
                """,
                (user_id,),
            ).fetchone()

        return str(row["total"])

    def activities_for_day(self, user_id: str, activity_date: date) -> list[dict]:
        with closing(self._connect()) as connection, connection:
            rows = connection.execute(
                """
                SELECT operation_id, user_id, activity_date, base_points,
                       value_points, reference_price, current_price,
                       reward_unit, uvi_transaction_id
                FROM daily_profile_activities
                WHERE user_id = ? AND activity_date = ?
                ORDER BY created_at, operation_id
                """,
                (user_id, activity_date.isoformat()),
            ).fetchall()

        return [dict(row) for row in rows]
