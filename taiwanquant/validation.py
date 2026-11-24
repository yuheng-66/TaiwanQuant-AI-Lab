"""Predeclared, expanding walk-forward windows on observed market sessions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Fold:
    train_start: date
    train_end: date
    valid_start: date
    valid_end: date

    def as_dict(self) -> dict[str, str]:
        return {field: getattr(self, field).isoformat()
                for field in ("train_start", "train_end", "valid_start", "valid_end")}


def expanding_folds(
    market_days: list[date], minimum_train_end: date, validation_end: date,
    count: int, sessions_per_fold: int, embargo_sessions: int,
) -> list[Fold]:
    """Build disjoint validation windows with a session gap before each one.

    The gap prevents overlapping train/validation score windows. Known prices
    inside the gap remain valid feature history at a later decision time.
    """
    if count < 2 or sessions_per_fold < 2 or embargo_sessions < 0:
        raise ValueError("invalid fold count, length or embargo")
    days = sorted(set(day for day in market_days if day <= validation_end))
    if not days or days[0] >= minimum_train_end:
        raise ValueError("minimum training end is outside market history")
    if days[-1] != validation_end:
        raise ValueError("validation end must be an observed market session")
    first_valid = len(days) - count * sessions_per_fold - (count - 1) * embargo_sessions
    if first_valid < 0:
        raise ValueError("not enough market sessions for requested folds")
    folds = []
    for index in range(count):
        valid_start = first_valid + index * (sessions_per_fold + embargo_sessions)
        train_end = valid_start - embargo_sessions - 1
        if train_end < 0 or days[train_end] < minimum_train_end:
            raise ValueError("not enough training sessions before first validation fold")
        folds.append(Fold(days[0], days[train_end], days[valid_start],
                          days[valid_start + sessions_per_fold - 1]))
    return folds
