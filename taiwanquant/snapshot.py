"""Capture licensed public daily quote snapshots with observed retrieval times."""

from __future__ import annotations

import hashlib
import json
import urllib.request
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

SOURCES = {
    "twse": {
        "url": "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL",
        "dataset": "https://data.gov.tw/dataset/11549",
        "date_field": "Date",
        "required": {"Date", "Code", "OpeningPrice", "ClosingPrice", "TradeVolume"},
    },
    "tpex": {
        "url": "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_quotes",
        "dataset": "https://data.gov.tw/dataset/11371",
        "date_field": "Date",
        "required": {"Date", "SecuritiesCompanyCode", "Open", "Close", "TradingShares"},
    },
}
MAX_BYTES = 5_000_000


def roc_date(value: str) -> date:
    """Parse ROC YYYYMMDD-style dates, e.g. 1151124 -> 2026-11-24."""
    if len(value) != 7 or not value.isascii() or not value.isdigit():
        raise ValueError(f"invalid ROC date: {value!r}")
    return date(int(value[:3]) + 1911, int(value[3:5]), int(value[5:7]))


def validate_payload(payload: bytes, market: str) -> tuple[list[dict], list[str]]:
    if market not in SOURCES:
        raise ValueError(f"unknown market: {market}")
    if len(payload) > MAX_BYTES:
        raise ValueError("snapshot exceeds 5 MB limit")
    rows = json.loads(payload)
    if not isinstance(rows, list) or not rows:
        raise ValueError("expected a nonempty JSON array")
    source = SOURCES[market]
    dates = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not source["required"].issubset(row):
            raise ValueError(f"row {index} lacks required fields")
        dates.add(roc_date(str(row[source["date_field"]])).isoformat())
    return rows, sorted(dates)


def capture(
    market: str,
    output_dir: Path,
    opener: Callable = urllib.request.urlopen,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> tuple[Path, Path]:
    """Write raw response and manifest without overwriting earlier evidence."""
    if market not in SOURCES:
        raise ValueError(f"unknown market: {market}")
    source = SOURCES[market]
    request = urllib.request.Request(
        source["url"], headers={"User-Agent": "TaiwanQuant-AI-Lab/0.1 (research)"}
    )
    with opener(request, timeout=20) as response:
        payload = response.read(MAX_BYTES + 1)
    retrieved_at = clock().astimezone(timezone.utc)
    rows, dates = validate_payload(payload, market)
    stamp = retrieved_at.strftime("%Y%m%dT%H%M%S%fZ")
    destination = output_dir / market
    destination.mkdir(parents=True, exist_ok=True)
    raw_path = destination / f"{stamp}.json"
    manifest_path = destination / f"{stamp}.manifest.json"
    manifest = {
        "market": market,
        "source_url": source["url"],
        "dataset_page": source["dataset"],
        "license_url": "https://data.gov.tw/license",
        "retrieved_at_utc": retrieved_at.isoformat(),
        "observed_market_dates": dates,
        "row_count": len(rows),
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
        "publication_time_known": False,
        "note": "Retrieval time is observed; historical publication time is unknown.",
    }
    # Exclusive create prevents an unlikely timestamp collision from replacing evidence.
    with raw_path.open("xb") as f:
        f.write(payload)
    try:
        with manifest_path.open("x", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
            f.write("\n")
    except Exception:
        raw_path.unlink()
        raise
    return raw_path, manifest_path
