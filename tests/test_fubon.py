import json
import tempfile
import unittest
from pathlib import Path

from taiwanquant.fubon import inspect_candles


class FubonInspectorTests(unittest.TestCase):
    def make_file(self, directory, **changes):
        payload = {
            "symbol": "2330", "type": "EQUITY", "exchange": "TWSE",
            "market": "TSE", "timeframe": "D", "adjusted": False,
            "data": [{"date": "2024-01-02", "open": 10, "close": 11,
                      "volume": 1000}],
        }
        payload.update(changes)
        path = Path(directory) / "export.json"
        path.write_text(json.dumps(payload))
        return path

    def test_inspects_daily_shares_without_returning_quotes(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = inspect_candles(self.make_file(tmp), "2330")
            self.assertEqual(result["row_count"], 1)
            self.assertEqual(result["first_date"], "2024-01-02")
            self.assertNotIn("open", result)
            self.assertFalse(result["publication_timestamps_present"])

    def test_rejects_adjusted_or_minute_candles(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "adjusted"):
                inspect_candles(self.make_file(tmp, adjusted=True), "2330")
            with self.assertRaisesRegex(ValueError, "timeframe"):
                inspect_candles(self.make_file(tmp, timeframe="1"), "2330")

    def test_rejects_invalid_volume(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.make_file(tmp, data=[{"date": "2024-01-02",
                                              "open": 10, "close": 11,
                                              "volume": 1.5}])
            with self.assertRaisesRegex(ValueError, "share volume"):
                inspect_candles(path, "2330")


if __name__ == "__main__":
    unittest.main()
