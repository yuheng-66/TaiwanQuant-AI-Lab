import unittest
from datetime import date, timedelta

from taiwanquant.validation import expanding_folds


class WalkForwardTests(unittest.TestCase):
    def test_disjoint_windows_and_embargo(self):
        days = [date(2024, 1, 1) + timedelta(days=i) for i in range(35)]
        folds = expanding_folds(days, days[10], days[29], 3, 4, 2)
        self.assertEqual(len(folds), 3)
        self.assertEqual(folds[-1].valid_end, days[29])
        for fold in folds:
            train_end_index = days.index(fold.train_end)
            valid_start_index = days.index(fold.valid_start)
            self.assertEqual(valid_start_index - train_end_index - 1, 2)
            self.assertLess(fold.train_end, fold.valid_start)
        for left, right in zip(folds, folds[1:]):
            self.assertLess(left.valid_end, right.valid_start)

    def test_insufficient_history_is_rejected(self):
        days = [date(2024, 1, 1) + timedelta(days=i) for i in range(15)]
        with self.assertRaisesRegex(ValueError, "not enough"):
            expanding_folds(days, days[10], days[-1], 3, 4, 2)

    def test_holdout_days_are_excluded(self):
        days = [date(2024, 1, 1) + timedelta(days=i) for i in range(35)]
        folds = expanding_folds(days, days[5], days[29], 2, 5, 1)
        self.assertTrue(all(fold.valid_end <= days[29] for fold in folds))


if __name__ == "__main__":
    unittest.main()
