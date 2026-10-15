"""Validated 10-stage release schedule for native 2FUNC."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from .supply import MAX_SUPPLY


STAGE_COUNT = 10
MIN_STAGE_INTERVAL_MONTHS = 6


class ReleaseScheduleError(ValueError):
    """Raised when a 2FUNC release schedule violates its contract."""


def calculate_approved_geometric_stage_amounts() -> tuple[int, ...]:
    """Calculate the approved 10-stage allocation; never mint coins."""
    ratio = Decimal("0.9")
    weights = tuple(ratio ** i for i in range(STAGE_COUNT))
    total_weight = sum(weights, Decimal("0"))

    amounts = [
        int(
            (Decimal(MAX_SUPPLY) * weight / total_weight).quantize(
                Decimal("1"), rounding=ROUND_HALF_UP
            )
        )
        for weight in weights
    ]

    # Preserve the previously accepted allocation and exact total supply.
    amounts[7] += MAX_SUPPLY - sum(amounts)

    if any(amount <= 0 for amount in amounts):
        raise ReleaseScheduleError("calculated amounts must be positive")
    if sum(amounts) != MAX_SUPPLY:
        raise ReleaseScheduleError("calculated amounts must equal MAX_SUPPLY")

    return tuple(amounts)


@dataclass(frozen=True)
class ReleaseStage:
    number: int
    start_date: date
    amount: int


class TwoFuncReleaseSchedule:
    """Validate an explicitly supplied schedule; never mint coins."""

    def __init__(self, stages: list[ReleaseStage]):
        if len(stages) != STAGE_COUNT:
            raise ReleaseScheduleError(
                f"exactly {STAGE_COUNT} release stages are required"
            )

        expected_numbers = list(range(1, STAGE_COUNT + 1))
        actual_numbers = [stage.number for stage in stages]

        if actual_numbers != expected_numbers:
            raise ReleaseScheduleError(
                "stage numbers must be ordered consecutively from 1 to 10"
            )

        for stage in stages:
            if isinstance(stage.amount, bool) or not isinstance(stage.amount, int):
                raise ReleaseScheduleError("stage amounts must be integers")
            if stage.amount <= 0:
                raise ReleaseScheduleError("stage amounts must be positive")

        for previous, current in zip(stages, stages[1:]):
            months = (
                (current.start_date.year - previous.start_date.year) * 12
                + current.start_date.month
                - previous.start_date.month
            )
            if months < MIN_STAGE_INTERVAL_MONTHS:
                raise ReleaseScheduleError(
                    "successive stages must start at least six months apart"
                )

        total = sum(stage.amount for stage in stages)
        if total != MAX_SUPPLY:
            raise ReleaseScheduleError(
                f"stage amounts must total exactly {MAX_SUPPLY}; got {total}"
            )

        self._stages = tuple(stages)

    @property
    def stages(self) -> tuple[ReleaseStage, ...]:
        return self._stages

    @property
    def total_scheduled(self) -> int:
        return sum(stage.amount for stage in self._stages)

    def stage(self, number: int) -> ReleaseStage:
        if isinstance(number, bool) or not isinstance(number, int):
            raise ReleaseScheduleError("stage number must be an integer")
        if not 1 <= number <= STAGE_COUNT:
            raise ReleaseScheduleError("stage number must be between 1 and 10")
        return self._stages[number - 1]

    def next_stage_eligible(
        self,
        as_of: date,
        issued_amount_by_stage: dict[int, int],
    ) -> ReleaseStage | None:
        """Return the next sequential stage when both release gates are met.

        The latest stage with a positive issuance is treated as the active
        stage. Stage 1 is the initial stage when no issuance record exists.
        This method checks eligibility only; it never issues coins.
        """
        import calendar

        if not isinstance(as_of, date):
            raise ReleaseScheduleError("as_of must be a date")
        if not isinstance(issued_amount_by_stage, dict):
            raise ReleaseScheduleError(
                "issued_amount_by_stage must be a dictionary"
            )

        for number, issued in issued_amount_by_stage.items():
            if isinstance(number, bool) or not isinstance(number, int):
                raise ReleaseScheduleError("issued stage numbers must be integers")
            if not 1 <= number <= STAGE_COUNT:
                raise ReleaseScheduleError(
                    "issued stage number must be between 1 and 10"
                )
            if isinstance(issued, bool) or not isinstance(issued, int):
                raise ReleaseScheduleError("issued amounts must be integers")
            if issued < 0:
                raise ReleaseScheduleError("issued amounts cannot be negative")
            if issued > self.stage(number).amount:
                raise ReleaseScheduleError(
                    "issued amount cannot exceed that stage's allocation"
                )

        # The first stage is the initial stage; positive issuance in a later
        # stage identifies the latest stage that has actually started.
        started_numbers = [
            number for number, amount in issued_amount_by_stage.items()
            if amount > 0
        ]
        previous_number = max(started_numbers, default=1)
        previous = self.stage(previous_number)

        if previous.start_date > as_of or previous_number == STAGE_COUNT:
            return None

        issued = issued_amount_by_stage.get(previous_number, 0)
        if issued * 100 < previous.amount * 90:
            return None

        month_index = (
            previous.start_date.year * 12
            + previous.start_date.month - 1
            + MIN_STAGE_INTERVAL_MONTHS
        )
        year, month_zero = divmod(month_index, 12)
        month = month_zero + 1
        day = min(
            previous.start_date.day,
            calendar.monthrange(year, month)[1],
        )
        if as_of < date(year, month, day):
            return None

        return self.stage(previous_number + 1)

    def due_stages(self, as_of: date) -> tuple[ReleaseStage, ...]:
        """Return stages whose start date has arrived; never issue coins."""
        if not isinstance(as_of, date):
            raise ReleaseScheduleError("as_of must be a date")
        return tuple(
            stage for stage in self._stages
            if stage.start_date <= as_of
        )
