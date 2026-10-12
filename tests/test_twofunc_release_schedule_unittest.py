import unittest
from datetime import date

from financial_core.blockchain.twofunc_supply import MAX_SUPPLY
from financial_core.blockchain.twofunc_release_schedule import (
    ReleaseStage,
    ReleaseScheduleError,
    TwoFuncReleaseSchedule,
)


def valid_test_stages():
    # Unequal test fixture only; NOT the approved production allocation.
    weights = [10, 9, 8, 7, 6, 5, 4, 3, 2, 1]
    amounts = [MAX_SUPPLY * w // sum(weights) for w in weights]
    amounts[-1] += MAX_SUPPLY - sum(amounts)

    return [
        ReleaseStage(
            number=i + 1,
            start_date=date(2027 + (i // 2), 1 + (i % 2) * 6, 1),
            amount=amounts[i],
        )
        for i in range(10)
    ]


class TwoFuncReleaseScheduleTests(unittest.TestCase):
    def test_accepts_ten_stages_with_exact_total(self):
        schedule = TwoFuncReleaseSchedule(valid_test_stages())
        self.assertEqual(len(schedule.stages), 10)
        self.assertEqual(schedule.total_scheduled, MAX_SUPPLY)

    def test_rejects_wrong_stage_count(self):
        with self.assertRaises(ReleaseScheduleError):
            TwoFuncReleaseSchedule(valid_test_stages()[:9])

    def test_rejects_out_of_order_stage_numbers(self):
        stages = valid_test_stages()
        stages[0] = ReleaseStage(2, stages[0].start_date, stages[0].amount)
        with self.assertRaises(ReleaseScheduleError):
            TwoFuncReleaseSchedule(stages)

    def test_rejects_total_above_supply(self):
        stages = valid_test_stages()
        last = stages[-1]
        stages[-1] = ReleaseStage(
            last.number, last.start_date, last.amount + 1
        )
        with self.assertRaises(ReleaseScheduleError):
            TwoFuncReleaseSchedule(stages)

    def test_rejects_non_positive_amount(self):
        stages = valid_test_stages()
        first = stages[0]
        stages[0] = ReleaseStage(first.number, first.start_date, 0)
        with self.assertRaises(ReleaseScheduleError):
            TwoFuncReleaseSchedule(stages)

    def test_rejects_stage_interval_under_six_months(self):
        stages = valid_test_stages()
        second = stages[1]
        stages[1] = ReleaseStage(
            second.number, date(2027, 6, 1), second.amount
        )
        with self.assertRaises(ReleaseScheduleError):
            TwoFuncReleaseSchedule(stages)

    def test_rejects_invalid_stage_lookup(self):
        schedule = TwoFuncReleaseSchedule(valid_test_stages())
        with self.assertRaises(ReleaseScheduleError):
            schedule.stage(11)



    def test_next_stage_requires_90_percent_and_six_months(self):
        stages = valid_test_stages()
        schedule = TwoFuncReleaseSchedule(stages)
        previous = stages[0]
        next_stage = stages[1]
        ninety_percent = (previous.amount * 90 + 99) // 100

        # Six months have elapsed, but less than 90% was issued.
        self.assertIsNone(
            schedule.next_stage_eligible(
                date(2027, 7, 1),
                {1: ninety_percent - 1},
            )
        )

        # At least 90% was issued, but six months have not elapsed.
        self.assertIsNone(
            schedule.next_stage_eligible(
                date(2027, 6, 30),
                {1: ninety_percent},
            )
        )

        # Both conditions are met.
        self.assertEqual(
            schedule.next_stage_eligible(
                date(2027, 7, 1),
                {1: ninety_percent},
            ),
            next_stage,
        )

    def test_next_stage_rejects_issued_amount_above_allocation(self):
        stages = valid_test_stages()
        schedule = TwoFuncReleaseSchedule(stages)

        with self.assertRaises(ReleaseScheduleError):
            schedule.next_stage_eligible(
                date(2027, 7, 1),
                {1: stages[0].amount + 1},
            )


if __name__ == "__main__":
    unittest.main()
