"""As-printed bars for one name, and a synthetic builder for tests and
controls. The engine reads this and nothing else about a market.

``day`` is the box: bars sharing a ``day`` are one session. Daily bars have
one bar per day; an intraday fixture has several. Instants (D10) arrive
with M4.4 — at M3 a bar's position in its day is an ordinal.
"""

from __future__ import annotations

from dataclasses import dataclass

import zlib

import numpy as np


@dataclass(frozen=True)
class Bars:
    name: str
    open: tuple[float, ...]
    high: tuple[float, ...]
    low: tuple[float, ...]
    close: tuple[float, ...]
    volume: tuple[float, ...]
    day: tuple[int, ...]
    close_at: tuple[str, ...] | None = None  # UTC close instants, ISO 8601 (D10, M4.4)

    def __post_init__(self):
        n = len(self.open)
        for f in ("high", "low", "close", "volume", "day"):
            if len(getattr(self, f)) != n:
                raise ValueError(f"{f} has {len(getattr(self, f))} bars, open has {n}")
        if self.close_at is not None:
            if len(self.close_at) != n:
                raise ValueError("close_at must have one instant per bar")
            from occams.data.instants import instant
            from datetime import datetime
            for t in self.close_at:
                instant(datetime.fromisoformat(t))  # raises NotAnInstant on a naive or date-only value
        for i in range(n):
            if not (self.low[i] <= min(self.open[i], self.close[i]) and self.high[i] >= max(self.open[i], self.close[i])):
                raise ValueError(f"bar {i} of {self.name} is not a bar: low/high do not enclose open/close")
        if any(self.day[i] > self.day[i + 1] for i in range(n - 1)):
            raise ValueError("days must be non-decreasing")

    @property
    def n(self) -> int:
        return len(self.open)

    @property
    def days(self) -> int:
        return len(set(self.day))

    def boxes(self) -> list[tuple[int, int, int]]:
        """(day, first_index, last_index) per session, in order."""
        out = []
        start = 0
        for i in range(1, self.n + 1):
            if i == self.n or self.day[i] != self.day[start]:
                out.append((self.day[start], start, i - 1))
                start = i
        return out


def random_walk(name: str, *, days: int, seed: int, sigma_daily: float, drift_daily: float = 0.0,
                start: float = 100.0, range_fraction: float = 0.5) -> Bars:
    """Daily bars: each close is the prior close times ``exp(drift + sigma z)``;
    the open is the prior close; high and low extend beyond open/close by a
    declared fraction of the move. Deterministic for a seed."""
    rng = np.random.default_rng([seed, zlib.crc32(name.encode("utf-8"))])  # stable across processes
    r = drift_daily + sigma_daily * rng.standard_normal(days)
    closes = start * np.exp(np.cumsum(r))
    opens = np.concatenate(([start], closes[:-1]))
    span = np.abs(closes - opens) * range_fraction + start * sigma_daily * 0.25 * rng.random(days)
    highs = np.maximum(opens, closes) + span
    lows = np.minimum(opens, closes) - span
    vol = np.full(days, 1e6)
    return Bars(name, tuple(map(float, opens)), tuple(map(float, highs)), tuple(map(float, lows)),
                tuple(map(float, closes)), tuple(map(float, vol)), tuple(range(days)))
