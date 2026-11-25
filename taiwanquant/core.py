"""Immutable market data validation and a fixed, long-only evaluation harness."""

from __future__ import annotations

import csv
import hashlib
import math
import time as clock
from bisect import insort
from dataclasses import dataclass
from datetime import date, datetime, time, timezone, timedelta
from pathlib import Path

TPE = timezone(timedelta(hours=8))
MAX_INPUT_BYTES = 100_000_000
MAX_BARS = 250_000


@dataclass(frozen=True)
class Bar:
    day: date
    symbol: str
    open: float
    close: float
    volume: int
    available_at: datetime


@dataclass(frozen=True)
class Costs:
    commission: float = 0.001425  # conservative, configurable assumption
    sell_tax: float = 0.003       # listed stock, non-day-trading assumption
    slippage: float = 0.001       # illustrative assumption per side
    max_volume_fraction: float = 0.01
    lot_size: int = 1000


def load_bars(path: str | Path) -> tuple[list[Bar], str]:
    path = Path(path)
    if path.stat().st_size > MAX_INPUT_BYTES:
        raise ValueError("dataset exceeds 100 MB input limit")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    bars: list[Bar] = []
    seen: set[tuple[date, str]] = set()
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"date", "symbol", "open", "close", "volume", "available_at"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"missing columns: {sorted(required - set(reader.fieldnames or []))}")
        for line, row in enumerate(reader, 2):
            if len(bars) >= MAX_BARS:
                raise ValueError(f"dataset exceeds {MAX_BARS} row limit")
            try:
                day = date.fromisoformat(row["date"])
                symbol = row["symbol"].strip()
                opening, closing = float(row["open"]), float(row["close"])
                volume = int(row["volume"])
                available = datetime.fromisoformat(row["available_at"])
                if not symbol or not (math.isfinite(opening) and math.isfinite(closing)):
                    raise ValueError("invalid symbol or non-finite price")
                if opening <= 0 or closing <= 0 or volume < 0 or available.tzinfo is None:
                    raise ValueError("prices must be positive; volume nonnegative; timestamp offset required")
                if (day, symbol) in seen:
                    raise ValueError("duplicate date/symbol")
                if available.astimezone(TPE).date() < day:
                    raise ValueError("availability precedes market date")
                seen.add((day, symbol))
                bars.append(Bar(day, symbol, opening, closing, volume, available))
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"line {line}: {exc}") from exc
    if not bars:
        raise ValueError("empty dataset")
    return sorted(bars, key=lambda b: (b.day, b.symbol)), digest


def evaluate(
    bars: list[Bar], start: date, end: date, lookback: int, top_n: int,
    costs: Costs = Costs(), initial_cash: float = 10_000_000,
    deadline: float | None = None,
) -> dict:
    """Rank close-to-close momentum at 18:00 TPE; fill at next session open.

    A missing row cannot be traded. Existing shares use the last known close for
    marking, which is flagged as a limitation in the project documentation.
    """
    if not 2 <= lookback <= 252 or top_n < 1 or start > end:
        raise ValueError("invalid strategy or window")
    if initial_cash <= 0 or not 0 <= costs.max_volume_fraction <= 1:
        raise ValueError("invalid capital or participation cap")
    if (costs.lot_size < 1 or any(not math.isfinite(value) or not 0 <= value < 0.1
                                for value in (costs.commission, costs.sell_tax,
                                              costs.slippage))):
        raise ValueError("invalid transaction cost or lot size")
    by_day: dict[date, dict[str, Bar]] = {}
    for index, b in enumerate(bars):
        if deadline is not None and index % 1024 == 0 and clock.monotonic() >= deadline:
            raise TimeoutError("experiment wall-time budget exhausted")
        by_day.setdefault(b.day, {})[b.symbol] = b
    days = sorted(by_day)
    history: dict[str, list[tuple[date, float]]] = {}
    published_volume: dict[str, tuple[date, int]] = {}
    releases = sorted(bars, key=lambda b: (b.available_at, b.day, b.symbol))
    release_index = 0
    cash = initial_cash
    shares: dict[str, int] = {}
    last_close: dict[str, float] = {}
    pending: list[str] | None = None
    equity: list[float] = []
    trades = 0
    total_cost = 0.0
    for day in days:
        if deadline is not None and clock.monotonic() >= deadline:
            raise TimeoutError("experiment wall-time budget exhausted")
        today = by_day[day]
        if start <= day <= end and pending is not None:
            eligible = {s: today[s] for s in pending if s in today and today[s].volume > 0}
            # Exit positions absent from the target only when a tradable row exists.
            for symbol in sorted(list(shares)):
                b = today.get(symbol)
                if symbol in pending or b is None or b.volume <= 0:
                    continue
                known_volume = published_volume.get(symbol, (day, 0))[1]
                cap = int(known_volume * costs.max_volume_fraction // costs.lot_size) * costs.lot_size
                qty = min(shares[symbol], cap)
                if qty:
                    gross = qty * b.open * (1 - costs.slippage)
                    fee = gross * (costs.commission + costs.sell_tax)
                    cash += gross - fee
                    total_cost += qty * b.open - gross + fee
                    shares[symbol] -= qty
                    if not shares[symbol]:
                        del shares[symbol]
                    trades += 1
            if eligible:
                marked = cash + sum(q * today[s].open if s in today else q * last_close[s]
                                    for s, q in shares.items())
                target_value = marked / len(pending)
                for symbol in sorted(eligible):
                    b = eligible[symbol]
                    current = shares.get(symbol, 0)
                    desired = max(0, int(target_value / (b.open * (1 + costs.slippage))
                                         // costs.lot_size) * costs.lot_size)
                    known_volume = published_volume.get(symbol, (day, 0))[1]
                    cap = int(known_volume * costs.max_volume_fraction // costs.lot_size) * costs.lot_size
                    qty = min(max(0, desired - current), cap)
                    per_share = b.open * (1 + costs.slippage) * (1 + costs.commission)
                    qty = min(qty, int(cash / per_share // costs.lot_size) * costs.lot_size)
                    if qty:
                        cash -= qty * per_share
                        shares[symbol] = current + qty
                        total_cost += qty * (per_share - b.open)
                        trades += 1
        for symbol, b in today.items():
            last_close[symbol] = b.close
        if start <= day <= end:
            equity.append(cash + sum(q * last_close[s] for s, q in shares.items()))
        # Add late-arriving older bars only once observed; retain market-date order.
        asof = datetime.combine(day, time(18), TPE)
        while release_index < len(releases) and releases[release_index].available_at <= asof:
            b = releases[release_index]
            if b.day <= day:
                insort(history.setdefault(b.symbol, []), (b.day, b.close))
                if b.day >= published_volume.get(b.symbol, (date.min, 0))[0]:
                    published_volume[b.symbol] = (b.day, b.volume)
            release_index += 1
        ranked = []
        for symbol, values in history.items():
            if symbol not in today or len(values) < lookback:
                continue
            if today[symbol].available_at > asof:
                continue
            score = values[-1][1] / values[-lookback][1] - 1
            ranked.append((score, symbol))
        pending = [s for _, s in sorted(ranked, key=lambda item: (-item[0], item[1]))[:top_n]]
    if len(equity) < 2:
        raise ValueError("evaluation window needs at least two market dates")
    if deadline is not None and clock.monotonic() >= deadline:
        raise TimeoutError("experiment wall-time budget exhausted")
    returns = [equity[0] / initial_cash - 1]
    returns.extend(equity[i] / equity[i - 1] - 1 for i in range(1, len(equity)))
    mean = sum(returns) / len(returns)
    variance = sum((r - mean) ** 2 for r in returns) / len(returns)
    sharpe = mean / math.sqrt(variance) * math.sqrt(252) if variance > 0 else None
    peak = initial_cash
    max_drawdown = 0.0
    for value in equity:
        peak = max(peak, value)
        max_drawdown = min(max_drawdown, value / peak - 1)
    return {
        "sessions": len(equity), "trades": trades,
        "total_return": equity[-1] / initial_cash - 1,
        "sharpe": sharpe, "max_drawdown": max_drawdown,
        "total_cost_twd": round(total_cost, 2),
        "final_equity_twd": round(equity[-1], 2),
    }
