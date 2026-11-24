import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from taiwanquant.snapshot import SOURCES, capture, roc_date, validate_payload


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, size):
        return self.payload[:size]


class SnapshotTests(unittest.TestCase):
    def test_tpex_catalogue_mapping(self):
        self.assertEqual(SOURCES["tpex"]["dataset"], "https://data.gov.tw/dataset/11371")

    def test_roc_date(self):
        self.assertEqual(str(roc_date("1151124")), "2026-11-24")
        with self.assertRaises(ValueError):
            roc_date("1151332")

    def test_capture_preserves_bytes_and_observed_clock(self):
        payload = b'[{"Date":"1151124","Code":"2330","OpeningPrice":"1","ClosingPrice":"2","TradeVolume":"1000"}]'
        with tempfile.TemporaryDirectory() as tmp:
            raw, manifest = capture(
                "twse", Path(tmp), opener=lambda *_args, **_kwargs: FakeResponse(payload),
                clock=lambda: datetime(2026, 11, 24, 9, 0, tzinfo=timezone.utc),
            )
            metadata = json.loads(manifest.read_text())
            self.assertEqual(raw.read_bytes(), payload)
            self.assertEqual(metadata["raw_sha256"], hashlib.sha256(payload).hexdigest())
            self.assertEqual(metadata["observed_market_dates"], ["2026-11-24"])
            self.assertFalse(metadata["publication_time_known"])

    def test_rejects_invalid_schema_without_writing(self):
        with self.assertRaisesRegex(ValueError, "required fields"):
            validate_payload(b'[{"Date":"1151124"}]', "twse")
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                capture("twse", Path(tmp),
                        opener=lambda *_args, **_kwargs: FakeResponse(b"[]"))
            self.assertEqual(list(Path(tmp).rglob("*")), [])
