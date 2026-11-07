"""Finance-owned daily POINT settlement orchestration."""

import json
import sqlite3
import uuid

from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_FLOOR, localcontext


DEFAULT_DESTINATION = "Drika"
ALLOWED_DESTINATIONS = {
    "Drika", "SHIR", "ΣSHIR", "2FUNC", "Drik",
}
POINTS_PER_DRIKA = Decimal("4")


class DailySettlementService:
    def __init__(self, connection_factory, ledger):
        self.connection_factory = connection_factory
        self.ledger = ledger

    @staticmethod
    def _utc_now():
        return datetime.now(timezone.utc)

    @staticmethod
    def _utc_text(value):
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _decimal(value):
        try:
            result = Decimal(str(value))
        except (InvalidOperation, TypeError, ValueError) as exc:
            raise ValueError("Invalid POINT amount") from exc

        if not result.is_finite() or result < 0:
            raise ValueError("POINT amount must be finite and non-negative")

        return result

    def _daily_points(self, user_id, operational_date, connection):
        start = datetime.combine(
            operational_date, time.min, tzinfo=timezone.utc
        )
        end = start + timedelta(days=1)

        entries = self.ledger.user_entries(
            user_id, connection=connection
        )

        amounts = []
        seen = set()

        for entry in entries:
            if entry.currency != "POINT":
                continue

            if entry.transaction_type != "EARN":
                continue

            try:
                timestamp = datetime.fromisoformat(
                    str(entry.timestamp).replace("Z", "+00:00")
                )
            except (TypeError, ValueError) as exc:
                raise ValueError(
                    "Invalid ledger timestamp"
                ) from exc

            if timestamp.tzinfo is None:
                raise ValueError(
                    "Ledger timestamp must include a timezone"
                )

            timestamp = timestamp.astimezone(timezone.utc)

            if not start <= timestamp < end:
                continue

            metadata = entry.metadata or {}

            if metadata.get("value_flow") != "POINT_TO_2FUNC":
                continue

            if metadata.get("activity_validated") is not True:
                continue

            if metadata.get("fraud_invalidated") is True:
                continue

            transaction_id = entry.transaction_id
            if transaction_id in seen:
                continue

            seen.add(transaction_id)
            amounts.append(self._decimal(entry.amount))

        if not amounts:
            return Decimal("0")

        min_exponent = min(
            amount.as_tuple().exponent for amount in amounts
        )
        max_adjusted = max(
            amount.adjusted() for amount in amounts if amount
        ) if any(amount for amount in amounts) else 0

        precision = max(
            28,
            max_adjusted - min_exponent
            + len(str(len(amounts))) + 3,
        )

        with localcontext() as context:
            context.prec = precision
            return sum(amounts, Decimal("0"))

    @staticmethod
    def _process_remainder(
        connection, user_id, operational_date, daily_points
    ):
        existing = connection.execute(
            """
            SELECT daily_points, carry_in_points,
                   drika_amount, remainder_points
            FROM daily_point_settlements
            WHERE user_id = ? AND operational_date = ?
            """,
            (user_id, operational_date.isoformat()),
        ).fetchone()

        if existing:
            if Decimal(existing["daily_points"]) != daily_points:
                raise ValueError(
                    "Existing daily settlement conflicts with ledger total"
                )

            return {
                "daily_points": Decimal(existing["daily_points"]),
                "carry_in_points": Decimal(existing["carry_in_points"]),
                "drika_amount": Decimal(existing["drika_amount"]),
                "remainder_points": Decimal(existing["remainder_points"]),
            }

        previous = connection.execute(
            """
            SELECT remainder_points
            FROM daily_point_remainders
            WHERE user_id = ? AND operational_date < ?
            ORDER BY operational_date DESC
            LIMIT 1
            """,
            (user_id, operational_date.isoformat()),
        ).fetchone()

        carry = (
            Decimal(previous["remainder_points"])
            if previous else Decimal("0")
        )

        min_exponent = min(
            daily_points.as_tuple().exponent,
            carry.as_tuple().exponent,
        )
        nonzero_values = [
            value for value in (daily_points, carry) if value
        ]
        max_adjusted = max(
            (value.adjusted() for value in nonzero_values),
            default=0,
        )

        precision = max(
            28,
            max_adjusted - min_exponent + 4,
        )

        with localcontext() as context:
            context.prec = precision
            combined = daily_points + carry
            drika = (
                combined / POINTS_PER_DRIKA
            ).to_integral_value(rounding=ROUND_FLOOR)
            remainder = combined - (
                drika * POINTS_PER_DRIKA
            )

        now_text = datetime.now(timezone.utc).isoformat()

        connection.execute(
            """
            INSERT INTO daily_point_settlements (
                user_id, operational_date, daily_points,
                carry_in_points, drika_amount, remainder_points,
                created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                operational_date.isoformat(),
                str(daily_points),
                str(carry),
                str(drika),
                str(remainder),
                now_text,
            ),
        )

        connection.execute(
            """
            INSERT INTO daily_point_remainders (
                user_id, operational_date, remainder_points,
                updated_at_utc
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, operational_date)
            DO UPDATE SET
                remainder_points = excluded.remainder_points,
                updated_at_utc = excluded.updated_at_utc
            """,
            (
                user_id,
                operational_date.isoformat(),
                str(remainder),
                now_text,
            ),
        )

        return {
            "daily_points": daily_points,
            "carry_in_points": carry,
            "drika_amount": drika,
            "remainder_points": remainder,
        }

    def create_previous_day_intent(self, user_id, now=None):
        if not user_id:
            raise ValueError("user_id is required")

        now = now or self._utc_now()
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")

        now = now.astimezone(timezone.utc)
        operational_date = now.date() - timedelta(days=1)
        day_text = operational_date.isoformat()

        operation_id = str(uuid.uuid5(
            uuid.NAMESPACE_URL,
            f"2FUN:daily-settlement:{user_id}:{day_text}",
        ))

        connection = self.connection_factory()
        try:
            connection.row_factory = sqlite3.Row
            connection.execute("PRAGMA busy_timeout = 30000")
            connection.execute("BEGIN IMMEDIATE")

            existing = connection.execute(
                """
                SELECT * FROM daily_settlement_intents
                WHERE user_id = ? AND operational_date = ?
                """,
                (user_id, day_text),
            ).fetchone()

            if existing:
                connection.commit()
                return {
                    "status": "existing",
                    "settlement": dict(existing),
                }

            daily_points = self._daily_points(
                user_id, operational_date, connection
            )

            result = self._process_remainder(
                connection, user_id, operational_date, daily_points
            )

            choice = connection.execute(
                """
                SELECT destination
                FROM daily_settlement_choices
                WHERE user_id = ? AND operational_date = ?
                """,
                (user_id, day_text),
            ).fetchone()

            destination = (
                choice["destination"] if choice else DEFAULT_DESTINATION
            )

            if destination not in ALLOWED_DESTINATIONS:
                raise ValueError("Invalid settlement destination")

            trigger_reason = (
                "USER_SELECTED" if choice else "AUTO_DRIKA"
            )
            settlement_id = str(uuid.uuid4())

            metadata = {
                "origin": "platform_api",
                "daily_points": str(result["daily_points"]),
                "carry_in_points": str(result["carry_in_points"]),
                "drika_amount": str(result["drika_amount"]),
                "remainder_points": str(result["remainder_points"]),
            }

            connection.execute(
                """
                INSERT INTO daily_settlement_intents (
                    settlement_id, user_id, operational_date,
                    destination, status, trigger_reason,
                    operation_id, created_at_utc, metadata_json
                ) VALUES (?, ?, ?, ?, 'PENDING', ?, ?, ?, ?)
                """,
                (
                    settlement_id,
                    user_id,
                    day_text,
                    destination,
                    trigger_reason,
                    operation_id,
                    self._utc_text(now),
                    json.dumps(
                        metadata,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ),
                ),
            )

            row = connection.execute(
                """
                SELECT * FROM daily_settlement_intents
                WHERE settlement_id = ?
                """,
                (settlement_id,),
            ).fetchone()

            connection.commit()

            return {
                "status": "created",
                "settlement": dict(row),
            }

        except sqlite3.IntegrityError:
            connection.rollback()

            row = connection.execute(
                """
                SELECT * FROM daily_settlement_intents
                WHERE user_id = ? AND operational_date = ?
                """,
                (user_id, day_text),
            ).fetchone()

            if row:
                return {
                    "status": "existing",
                    "settlement": dict(row),
                }

            raise

        except Exception:
            connection.rollback()
            raise

        finally:
            connection.close()
