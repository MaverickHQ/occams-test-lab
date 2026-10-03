"""Three configured partitions over the archive — definition, measurement,
reserve — stamped into every result (D11, ADR-0006, ADR-0031, M4.6). The
forward window is wall-clock time from entry into FORWARD and is not one of
them; a config that supplies a fourth percentage is refused by the loader.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from occams.data.bars import Bars

NAMES = ("definition", "measurement", "reserve")
CALENDAR_FLOOR = 600_000   # an archive day below this is a bar index, not a calendar ordinal (pre ADR-0005 fix)


class CalendarNotFrozen(RuntimeError):
    """A partition would be cut from the archive's live span after one was
    already cut: the boundaries would move with the last bar ingested."""


class AlreadyFrozen(RuntimeError):
    pass


@dataclass(frozen=True)
class Partitions:
    definition: float
    measurement: float
    reserve: float

    def __post_init__(self):
        for n in NAMES:
            v = getattr(self, n)
            if not (0 < v < 1):
                raise ValueError(f"partition {n} must be in (0, 1)")
        if not math.isclose(self.definition + self.measurement + self.reserve, 1.0, rel_tol=0, abs_tol=1e-12):
            raise ValueError("partitions must sum to exactly 1")

    @classmethod
    def from_config(cls, cfg) -> "Partitions":
        return cls(cfg.partitions.definition, cfg.partitions.measurement, cfg.partitions.reserve)

    def bounds(self, n_days: int) -> dict[str, tuple[int, int]]:
        """Half-open day ranges [start, end), oldest first: definition,
        then measurement, then the reserve of most recent history."""
        d = int(round(n_days * self.definition))
        m = int(round(n_days * self.measurement))
        return {"definition": (0, d), "measurement": (d, d + m), "reserve": (d + m, n_days)}

    def bounds_over(self, lo: int, hi: int) -> dict[str, tuple[int, int]]:
        """Half-open day ranges over a common span [lo, hi] — one calendar for
        every series in the archive, so definition never overlaps measurement
        across names (ADR-0005)."""
        n = hi - lo + 1
        d = int(round(n * self.definition))
        m = int(round(n * self.measurement))
        return {"definition": (lo, lo + d), "measurement": (lo + d, lo + d + m), "reserve": (lo + d + m, hi + 1)}

    @staticmethod
    def common_span(bars_by_name) -> tuple[int, int]:
        days = [d for b in bars_by_name.values() for d in (b.day[0], b.day[-1])]
        return min(days), max(days)

    def slice(self, bars: Bars, partition: str, *, span: tuple[int, int] | None = None) -> tuple[Bars, tuple[int, int]]:
        """``span`` is the archive-wide (first day, last day); without it the
        series' own span is used, which is right for one series and wrong
        for a pooled set — pass the common span for anything pooled."""
        if partition not in NAMES:
            raise KeyError(f"{partition!r} is not a partition; the forward window is wall-clock time (ADR-0031)")
        if span is None:
            b = self.bounds_over(bars.day[0], bars.day[-1])[partition]
        else:
            b = self.bounds_over(*span)[partition]
        idx = [i for i, d in enumerate(bars.day) if b[0] <= d < b[1]]
        if not idx and span is None:
            raise ValueError(f"{partition} holds no bars for {bars.name}")
        # on a common span a name listed after the boundary simply has no bars here
        pick = lambda t: tuple(t[i] for i in idx)  # noqa: E731
        out = Bars(bars.name, pick(bars.open), pick(bars.high), pick(bars.low), pick(bars.close),
                   pick(bars.volume), pick(bars.day),
                   close_at=None if bars.close_at is None else pick(bars.close_at))
        return out, b

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.definition, self.measurement, self.reserve)


def slice_days(bars: Bars, lo: int, hi: int) -> Bars:
    """The bars whose day lies in [lo, hi) — a sub-window of a partition (M15.9)."""
    idx = [i for i, d in enumerate(bars.day) if lo <= d < hi]
    pick = lambda t: tuple(t[i] for i in idx)  # noqa: E731
    return Bars(bars.name, pick(bars.open), pick(bars.high), pick(bars.low), pick(bars.close), pick(bars.volume), pick(bars.day),
                close_at=None if bars.close_at is None else pick(bars.close_at))




# ---- ADR-0038: the calendar is frozen ------------------------------------------------

def frozen_calendar(register, universe: str = "") -> dict | None:
    """The latest ``CalendarFrozen`` record for ``universe`` ("" is the
    Register-wide calendar), or None."""
    recs = [r for r in register.records() if r["type"] == "CalendarFrozen" and r.get("universe", "") == universe]
    return recs[-1] if recs else None


def declared_universe(register, name: str) -> dict | None:
    recs = [r for r in register.records() if r["type"] == "UniverseDeclared" and r["name"] == name]
    return recs[-1] if recs else None


def span_for(register, bars_by_name, split: "Partitions", universe: str = "") -> tuple[int, int]:
    """The span partitions are cut from: the frozen calendar when one
    exists; otherwise the archive's live span, but only while that span
    reproduces every boundary the Register already used. A live span that
    would move a recorded boundary — the archive grew since the last cut —
    is refused by name: freeze the calendar first."""
    cal = frozen_calendar(register, universe)
    if cal is not None:
        return int(cal["start_day"]), int(cal["end_day"])
    live = Partitions.common_span(bars_by_name)
    bad = _mismatches(_recorded_cuts(register), split, *live) if not universe else []
    if bad:
        raise CalendarNotFrozen("the archive's live span would move a boundary the Register already used — "
                                + "; ".join(bad) + " (ADR-0038); run `python -m occams calendar freeze` first")
    return live


def _recorded_cuts(register) -> list[tuple[str, str, tuple[int, int]]]:
    out = []
    for r in register.records():
        if r["type"] == "ClassifierFrozen" and int(r["definition_start_day"]) >= CALENDAR_FLOOR:
            out.append(("ClassifierFrozen", "definition", (int(r["definition_start_day"]), int(r["definition_end_day"]))))
        if r["type"] == "ObservationsConsumed":
            out.append((f"ObservationsConsumed {r['hypothesis_id']}", r["partition"], (int(r["start_day"]), int(r["end_day"]))))
    return out


def _mismatches(cuts, split: "Partitions", lo: int, hi: int) -> list[str]:
    b = split.bounds_over(lo, hi)
    return [f"{who} cut {part} as [{lo_}, {hi_}) but this span cuts it as [{b[part][0]}, {b[part][1]})"
            for who, part, (lo_, hi_) in cuts if b[part] != (lo_, hi_)]


def freeze_calendar(register, bars_by_name, *, split: Partitions, config_sha: str, reason: str = "",
                    start: int | None = None, end: int | None = None, supersedes: str = "", universe: str = "") -> dict:
    """Freeze the span every partition is cut from. Refuses a span that
    would move a boundary the Register has already used, naming the end
    day that would reproduce it; refuses a second freeze that does not
    name the one it supersedes and say why."""
    current = frozen_calendar(register, universe)
    if current is not None:
        key = f"{current['start_day']}-{current['end_day']}"
        if supersedes != key or not reason.strip():
            raise AlreadyFrozen(f"a calendar is already frozen ({key}); freezing again is a recorded supersession — "
                                f"name it with supersedes={key!r} and give the reason (ADR-0038)")
    live = Partitions.common_span(bars_by_name) if bars_by_name else None
    if (start is None or end is None) and live is None:
        raise ValueError("no bars and no explicit span: nothing to freeze")
    lo = int(live[0] if start is None else start)
    hi = int(live[1] if end is None else end)
    if hi <= lo:
        raise ValueError("the calendar's end must be after its start")
    cuts = _recorded_cuts(register) if not universe else []   # a universe's cuts are its own; the Register-wide ones do not bind it
    bad = _mismatches(cuts, split, lo, hi)
    if bad:
        fits = [h for h in range(hi - 400, hi + 401) if h > lo and not _mismatches(cuts, split, lo, h)]
        hint = (f"; an end day in {fits[0]}..{fits[-1]} reproduces every recorded cut" if fits
                else "; no end day within 400 days reproduces every recorded cut — the split or the start moved")
        raise ValueError("a frozen calendar must reproduce every boundary the Register already used: " + "; ".join(bad) + hint)
    b = split.bounds_over(lo, hi)
    rec = register.CalendarFrozen(lo, hi, b["definition"][1], b["measurement"][1], split.as_tuple(),
                                  tuple(sorted(bars_by_name)), config_sha, reason, supersedes, universe)
    register.append(rec)
    return frozen_calendar(register, universe)
