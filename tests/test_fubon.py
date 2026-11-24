import json
import tempfile
import unittest
from pathlib import Path
from datetime import date, datetime, timezone

from taiwanquant.fubon import fetch_daily_candles, inspect_candles


class FubonInspectorTests(unittest.TestCase):
    def make_file(self, directory, **changes):
        payload = {
            "symbol": "2330", "type": "EQUITY", "exchange": "TWSE",
            "market": "TSE", "timeframe": "D", "adjusted": False,
            "data": [{"date": "2024-01-02", "open": 10, "high": 12,
                      "low": 9, "close": 11,
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
                                              "open": 10, "high": 12, "low": 9,
                                              "close": 11,
                                              "volume": 1.5}])
            with self.assertRaisesRegex(ValueError, "share volume"):
                inspect_candles(path, "2330")

    def test_rejects_inconsistent_ohlc(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = self.make_file(tmp, data=[{"date": "2024-01-02",
                                              "open": 10, "high": 10.5,
                                              "low": 9, "close": 11,
                                              "volume": 1000}])
            with self.assertRaisesRegex(ValueError, "invalid price"):
                inspect_candles(path, "2330")

    def test_read_only_fetch_saves_private_provenance(self):
        class FakeHistory:
            def candles(self, **kwargs):
                self.request = kwargs
                return {
                    "symbol": "2330", "exchange": "TWSE", "timeframe": "D",
                    "data": [{"date": "2024-01-02", "open": 10,
                              "high": 12, "low": 9, "close": 11,
                              "volume": 1000}],
                }

        class FakeClient:
            historical = FakeHistory()

        with tempfile.TemporaryDirectory() as tmp:
            client = FakeClient()
            raw, manifest = fetch_daily_candles(
                client, "2330", date(2024, 1, 1), date(2024, 1, 31),
                Path(tmp), clock=lambda: datetime(2024, 2, 1, tzinfo=timezone.utc),
            )
            self.assertEqual(client.historical.request["adjusted"], "false")
            self.assertEqual(client.historical.request["timeframe"], "D")
            self.assertTrue(raw.exists())
            metadata = json.loads(manifest.read_text())
            self.assertFalse(metadata["redistribution_reviewed"])
            self.assertFalse(metadata["publication_timestamps_present"])

    def test_read_only_fetch_rejects_long_range_before_call(self):
        class FakeHistory:
            def candles(self, **_):
                raise AssertionError("broker must not be called")

        class FakeClient:
            historical = FakeHistory()

        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, "fewer than 365"):
                fetch_daily_candles(FakeClient(), "2330", date(2024, 1, 1),
                                    date(2025, 1, 1), Path(tmp))


if __name__ == "__main__":
    unittest.main()
