"""Offline validation for privately exported Fubon Neo daily candles."""

from __future__ import annotations

import json
import math
import hashlib
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable


def validate_candles(payload: dict, expected_symbol: str) -> dict:
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
            high = float(row["high"])
            low = float(row["low"])
            closing = float(row["close"])
            volume = float(row["volume"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid candle {index}: {exc}") from exc
        if day in dates or not all(map(math.isfinite, (opening, high, low, closing, volume))):
            raise ValueError(f"duplicate date or non-finite candle {index}")
        if (low <= 0 or low > min(opening, closing) or
                high < max(opening, closing) or volume < 0 or
                not volume.is_integer()):
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


def inspect_candles(path: str | Path, expected_symbol: str) -> dict:
    raw = Path(path).read_bytes()
    if len(raw) > 5_000_000:
        raise ValueError("Fubon export exceeds 5 MB inspection limit")
    return validate_candles(json.loads(raw), expected_symbol)


def fetch_daily_candles(
    authenticated_stock_client, symbol: str, start: date, end: date,
    output_dir: Path,
    clock: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
) -> tuple[Path, Path]:
    """Read only historical candles through an already-authenticated SDK client."""
    if not re.fullmatch(r"[0-9A-Za-z]{4,10}", symbol):
        raise ValueError("invalid Fubon symbol")
    if start > end or (end - start).days >= 365:
        raise ValueError("one request must span fewer than 365 days")
    request = {
        "symbol": symbol, "from": start.isoformat(), "to": end.isoformat(),
        "timeframe": "D", "adjusted": "false",
        "fields": "open,high,low,close,volume,turnover,change",
    }
    response = authenticated_stock_client.historical.candles(**request)
    metadata = validate_candles(response, symbol)
    if (date.fromisoformat(metadata["first_date"]) < start or
            date.fromisoformat(metadata["last_date"]) > end):
        raise ValueError("broker response contains dates outside requested range")
    encoded = json.dumps(response, separators=(",", ":"), ensure_ascii=False).encode()
    if len(encoded) > 5_000_000:
        raise ValueError("Fubon response exceeds 5 MB storage limit")
    retrieved_at = clock().astimezone(timezone.utc)
    stamp = retrieved_at.strftime("%Y%m%dT%H%M%S%fZ")
    destination = output_dir / symbol
    destination.mkdir(parents=True, exist_ok=True)
    base = f"{start.isoformat()}_{end.isoformat()}_{stamp}"
    raw_path = destination / f"{base}.json"
    manifest_path = destination / f"{base}.manifest.json"
    manifest = {
        **metadata,
        "source": "Fubon Neo authenticated historical/candles",
        "request": request,
        "retrieved_at_utc": retrieved_at.isoformat(),
        "sha256": hashlib.sha256(encoded).hexdigest(),
        "redistribution_reviewed": False,
        "usage": "private local research only",
    }
    with raw_path.open("xb") as f:
        f.write(encoded)
    try:
        with manifest_path.open("x", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
            f.write("\n")
    except Exception:
        raw_path.unlink()
        raise
    return raw_path, manifest_path
