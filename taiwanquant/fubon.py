"""Offline validation for privately exported Fubon Neo daily candles."""

from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path


def inspect_candles(path: str | Path, expected_symbol: str) -> dict:
    raw = Path(path).read_bytes()
    if len(raw) > 5_000_000:
        raise ValueError("Fubon export exceeds 5 MB inspection limit")
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("expected Fubon response object")
    if payload.get("symbol") != expected_symbol or payload.get("timeframe") != "D":
        raise ValueError("symbol or timeframe does not match a daily-candle request")
    if payload.get("adjusted") is True:
        raise ValueError("adjusted prices are not executable fill prices")
    if payload.get("exchange") not in {"TWSE", "TPEx", "TPEX"}:
        raise ValueError("unsupported exchange")
    rows = payload.get("data")
    if not isinstance(rows, list) or not rows:
        raise ValueError("expected nonempty candle data")
    dates = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError(f"candle {index} is not an object")
        try:
            day = date.fromisoformat(row["date"])
            opening = float(row["open"])
            closing = float(row["close"])
            volume = float(row["volume"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid candle {index}: {exc}") from exc
        if day in dates or not all(map(math.isfinite, (opening, closing, volume))):
            raise ValueError(f"duplicate date or non-finite candle {index}")
        if opening <= 0 or closing <= 0 or volume < 0 or not volume.is_integer():
            raise ValueError(f"invalid price or share volume in candle {index}")
        dates.add(day)
    return {
        "symbol": expected_symbol,
        "exchange": payload["exchange"],
        "timeframe": "D",
        "row_count": len(rows),
        "first_date": min(dates).isoformat(),
        "last_date": max(dates).isoformat(),
        "price_adjustment": "unadjusted_or_not_declared",
        "publication_timestamps_present": False,
    }
