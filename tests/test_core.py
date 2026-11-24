import csv
import json
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

from taiwanquant.__main__ import research, test_holdout
from taiwanquant.core import Bar, Costs, evaluate, load_bars

TPE = timezone(timedelta(hours=8))


def bar(day, close, opening=None, available_hour=17):
    return Bar(date.fromisoformat(day), "2330", opening or close, close, 2_000_000,
               datetime.fromisoformat(f"{day}T{available_hour:02d}:00:00+08:00"))


class EvaluatorTests(unittest.TestCase):
    def test_next_open_and_costs(self):
        rows = [bar("2024-01-01", 10), bar("2024-01-02", 20),
                bar("2024-01-03", 40, opening=40), bar("2024-01-04", 40)]
        free = Costs(0, 0, 0, 1, 1000)
        paid = Costs(0.001425, 0.003, 0.001, 1, 1000)
        no_cost = evaluate(rows, date(2024, 1, 1), date(2024, 1, 4), 2, 1, free)
        with_cost = evaluate(rows, date(2024, 1, 1), date(2024, 1, 4), 2, 1, paid)
        self.assertAlmostEqual(no_cost["total_return"], 0)
        self.assertLess(with_cost["total_return"], 0)
        self.assertGreater(with_cost["total_cost_twd"], 0)

    def test_expired_budget_stops_evaluation(self):
        rows = [bar("2024-01-01", 10), bar("2024-01-02", 20)]
        with self.assertRaisesRegex(TimeoutError, "budget exhausted"):
            evaluate(rows, date(2024, 1, 1), date(2024, 1, 2), 2, 1,
                     deadline=0.0)

    def test_negative_transaction_cost_is_rejected(self):
        rows = [bar("2024-01-01", 10), bar("2024-01-02", 20)]
        with self.assertRaisesRegex(ValueError, "transaction cost"):
            evaluate(rows, date(2024, 1, 1), date(2024, 1, 2), 2, 1,
                     Costs(commission=-0.01))

    def test_unpublished_bar_cannot_drive_signal(self):
        rows = [bar("2024-01-01", 10),
                Bar(date(2024, 1, 2), "2330", 20, 20, 2_000_000,
                    datetime(2024, 1, 4, 17, tzinfo=TPE)),
                bar("2024-01-03", 40), bar("2024-01-04", 40)]
        result = evaluate(rows, date(2024, 1, 1), date(2024, 1, 3), 2, 1)
        self.assertEqual(result["trades"], 0)

    def test_late_bar_enters_history_only_after_retrieval(self):
        rows = [bar("2024-01-01", 10),
                Bar(date(2024, 1, 2), "2330", 20, 20, 2_000_000,
                    datetime(2024, 1, 3, 17, tzinfo=TPE)),
                bar("2024-01-03", 30), bar("2024-01-04", 40)]
        free = Costs(0, 0, 0, 1, 1000)
        early = evaluate(rows, date(2024, 1, 1), date(2024, 1, 3), 3, 1, free)
        later = evaluate(rows, date(2024, 1, 1), date(2024, 1, 4), 3, 1, free)
        self.assertEqual(early["trades"], 0)
        self.assertGreater(later["trades"], 0)

    def test_first_session_return_is_included(self):
        rows = [bar("2024-01-01", 10), bar("2024-01-02", 20),
                bar("2024-01-03", 30, opening=20), bar("2024-01-04", 30)]
        free = Costs(0, 0, 0, 1, 1000)
        result = evaluate(rows, date(2024, 1, 3), date(2024, 1, 4), 2, 1, free)
        self.assertGreater(result["total_return"], 0)

    def test_validator_rejects_duplicate_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bars.csv"
            path.write_text("date,symbol,open,close,volume,available_at\n"
                            "2024-01-01,2330,10,10,1000,2024-01-01T17:00:00+08:00\n"
                            "2024-01-01,2330,10,10,1000,2024-01-01T17:00:00+08:00\n")
            with self.assertRaisesRegex(ValueError, "duplicate"):
                load_bars(path)

    def test_research_records_every_trial_and_seals_holdout(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bars.csv"
            with path.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "symbol", "open", "close", "volume", "available_at"])
                for i in range(12):
                    day = date(2024, 1, 1) + timedelta(days=i)
                    writer.writerow([day, "2330", 10 + i, 10 + i, 2_000_000,
                                     f"{day}T17:00:00+08:00"])
            out = Path(tmp) / "run"
            research(SimpleNamespace(csv=str(path), out=str(out), train_end="2024-01-04",
                                     valid_end="2024-01-08", test_end="2024-01-12",
                                     max_trials=2, max_seconds=120))
            records = [json.loads(line) for line in (out / "experiments.jsonl").read_text().splitlines()]
            self.assertEqual(len(records), 2)
            self.assertTrue(all(record["status"] == "completed" for record in records))
            self.assertFalse((out / "holdout.json").exists())
            test_holdout(SimpleNamespace(csv=str(path), run=str(out)))
            self.assertTrue((out / "holdout.json").exists())
            with self.assertRaisesRegex(ValueError, "already been opened"):
                test_holdout(SimpleNamespace(csv=str(path), run=str(out)))

    def test_research_records_multiple_validation_folds(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bars.csv"
            with path.open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["date", "symbol", "open", "close", "volume", "available_at"])
                for i in range(100):
                    day = date(2024, 1, 1) + timedelta(days=i)
                    writer.writerow([day, "2330", 10 + i / 10, 10 + i / 10,
                                     2_000_000, f"{day}T17:00:00+08:00"])
            out = Path(tmp) / "run"
            research(SimpleNamespace(
                csv=str(path), out=str(out), train_end="2024-01-31",
                valid_end="2024-03-11", test_end="2024-04-09",
                max_trials=2, max_seconds=120, walk_forward_folds=2,
                fold_sessions=10, embargo_sessions=2,
            ))
            record = json.loads((out / "experiments.jsonl").read_text().splitlines()[0])
            self.assertEqual(len(record["folds"]), 2)
            self.assertEqual(record["status"], "completed")
            self.assertFalse((out / "holdout.json").exists())


if __name__ == "__main__":
    unittest.main()
