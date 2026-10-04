"""The probes: what a spec's geometry and gate yield with no entry rule at all (M16.9; the
review's F20). A *passive* probe is a market order on every box, one side. The guards' two
Monte Carlo distributions — beats-null's and the fifth check's — are built from these, and
so is the survey's readiness table; before this module each engine and the survey built
its own.

Beats-null (M16.14, ADR-0048): the winner against random entry — a coin's side on every box,
which is half the long passive outcome and half the short — summed by calendar day and
resampled together in blocks of days, at the winner's count.

The fifth check (M16.15, ADR-0049): the winner against the passive alternative at its **own
side mix** — always-long for a long-only entry, the coin's own expectation for a coin — by
the same resampling; and the margin in its two parts, *selection* and *execution*. The
surface a sweep optimises is measured against that same baseline: one number.

The day-boxed probes are audited for obtainability like any other fill and the
position-boxed ones are not, as built.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from occams import inference
from occams.data.actions import ActionSeries
from occams.spec.compile import CompiledStrategy, to_engine
from occams.spec.spec import EntryKind, ExitKind, Side

DAY_BOXED, POSITION_BOXED = "day_boxed", "position_boxed"
AUDITED = {DAY_BOXED: True, POSITION_BOXED: False}      # as built: only the day-boxed probes pass the fill auditor
_NO_ACTIONS = ActionSeries()


class ProbeRefusal(RuntimeError):
    """A probe produced nothing to draw from. The engines re-raise it as their own refusal."""


def _engine(name: str):
    from occams.engine import day_boxed, position_boxed

    return position_boxed if name == POSITION_BOXED else day_boxed


def _market(compiled: CompiledStrategy, entry) -> CompiledStrategy:
    spec = compiled.spec
    return to_engine(spec.replace(entries=(entry,), order_type=spec.order_type.__class__("market")))


def passive(compiled: CompiledStrategy, bars_by_name: dict, *, side: Side = Side.LONG, seed: int = 0, cost_in_r: float,
            actions: ActionSeries = _NO_ACTIONS, costs=None, regime=None):
    """A market order on every box, ``side``, under this spec's exits, stop, horizon and
    regime gate (ADR-0043, ADR-0045): always-long, or its mirror."""
    probe = _market(compiled, compiled.spec.entries[0].__class__(EntryKind.ALWAYS, side, ()))
    return _engine(compiled.engine).run(probe, bars_by_name, seed=seed, cost_in_r=cost_in_r, actions=actions, costs=costs,
                                        audit_fills=AUDITED[compiled.engine], regime=regime)


def calendar_of(bars_by_name: dict) -> np.ndarray:
    """Every calendar day of the partition, traded or not, in order: what a block of days is a run of."""
    return np.asarray(sorted({int(d) for bars in bars_by_name.values() for d in bars.day}))


def hold_of(compiled: CompiledStrategy, positions=()) -> int:
    """The bars a position is held: the spec's time exit — one for a day-boxed spec — or, where a
    spec has none, the length nineteen positions in twenty stay within."""
    if compiled.engine != POSITION_BOXED:
        return 1
    for x in compiled.spec.exits:
        if x.kind is ExitKind.TIME:
            return max(1, int(x.param("bars")))
    lengths = sorted(t.exit_index - t.entry_index + 1 for t in positions)
    return max(1, lengths[min(len(lengths) - 1, int(0.95 * len(lengths)))]) if lengths else 1


def against_random_entry(compiled: CompiledStrategy, bars_by_name: dict, winner_trades, *, longs, shorts, draws: int,
                         seed: int) -> inference.DayComparison:
    """Beats-null's comparison (ADR-0048): the winner against random entry at the same geometry and
    gate — every box the gate admits, the side by a fair coin, which in expectation is half the
    long outcome of every box and half the short. Winner and reference are summed by calendar
    day and resampled together in blocks of days."""
    if not longs or not shorts:
        raise ProbeRefusal("no boxes to draw a null from")
    return inference.compare_by_day(
        calendar_of(bars_by_name),
        winner=([t.day for t in winner_trades], [t.net_r for t in winner_trades]),
        reference=[([t.day for t in longs], [t.net_r for t in longs], 0.5), ([t.day for t in shorts], [t.net_r for t in shorts], 0.5)],
        hold=hold_of(compiled, longs), draws=draws, seed=seed, stream=48)


SIDE_MATCHED = "side_matched"


def long_share(records) -> float:
    """The share of a cell's trades that are long: one for a long-only entry, about a half for a coin."""
    records = list(records)
    return sum(1 for t in records if t.side is Side.LONG) / len(records) if records else 1.0


def summary(trades) -> tuple[float | None, tuple[tuple[str, float, int], ...]]:
    """One passive side's EV, pooled and per group, from its trades."""
    by: dict[str, list[float]] = {}
    for t in trades:
        by.setdefault(t.name, []).append(t.net_r)
    if not by:
        return None, ()
    pooled = sum(v for vs in by.values() for v in vs) / sum(len(vs) for vs in by.values())
    return pooled, tuple((g, sum(vs) / len(vs), len(vs)) for g, vs in sorted(by.items()))


def side_matched(longs, shorts, share: float) -> tuple[float | None, tuple[tuple[str, float, float], ...]]:
    """The passive alternative at a cell's own side mix (ADR-0049 §1): every admitted box, long
    and short, weighted ``share`` and ``1 - share``. For a long-only cell it is always-long,
    number for number; for a coin flip it is the coin's own expectation."""
    if share >= 1.0:
        return summary(longs)
    if share <= 0.0:
        return summary(shorts)
    by: dict[str, list[float]] = {}
    for weight, trades in ((share, longs), (1.0 - share, shorts)):
        for t in trades:
            acc = by.setdefault(t.name, [0.0, 0.0])
            acc[0] += weight * t.net_r
            acc[1] += weight
    if not by:
        return None, ()
    pooled = sum(s for s, _k in by.values()) / sum(k for _s, k in by.values())
    return pooled, tuple((g, s / k, k) for g, (s, k) in sorted(by.items()))


@dataclass(frozen=True)
class Baseline:
    """A cell's passive alternative: its EV, per group, the side mix it was matched to, and the probes it came from."""

    ev: float | None
    by_group: tuple
    share: float
    longs: tuple
    shorts: tuple | None        # None when the cell is long-only: the short probe was not needed, and was not run


def baseline_of(compiled: CompiledStrategy, bars_by_name: dict, records, *, seed: int = 0, cost_in_r: float,
                actions: ActionSeries = _NO_ACTIONS, costs=None, regime=None) -> Baseline:
    """The side-matched passive alternative for one cell's trades — what the surface's margin is
    measured against and what the fifth check tests against: one number (ADR-0049 §2)."""
    share = long_share(records)
    kw = dict(seed=seed, cost_in_r=cost_in_r, actions=actions, costs=costs, regime=regime)
    longs = passive(compiled, bars_by_name, side=Side.LONG, **kw)
    shorts = passive(compiled, bars_by_name, side=Side.SHORT, **kw) if share < 1.0 else None
    ev, by_group = side_matched(longs, shorts or (), share)
    return Baseline(ev, by_group, share, longs, shorts)


def against_passive(compiled: CompiledStrategy, bars_by_name: dict, winner_trades, baseline: Baseline, *, draws: int,
                    seed: int) -> inference.DayComparison:
    """The fifth check's comparison (ADR-0049 §3): the winner against the passive alternative at
    its own side mix, both summed by calendar day and resampled together in blocks of days."""
    if not baseline.longs:
        raise ProbeRefusal("no boxes to draw an always-long baseline from")
    reference = [([t.day for t in baseline.longs], [t.net_r for t in baseline.longs], baseline.share)]
    if baseline.share < 1.0:
        reference.append(([t.day for t in baseline.shorts], [t.net_r for t in baseline.shorts], 1.0 - baseline.share))
    return inference.compare_by_day(
        calendar_of(bars_by_name), winner=([t.day for t in winner_trades], [t.net_r for t in winner_trades]),
        reference=reference, hold=hold_of(compiled, baseline.longs), draws=draws, seed=seed, stream=49)


def execution_part(compiled: CompiledStrategy, bars_by_name: dict, records, *, cost_in_r: float,
                   actions: ActionSeries = _NO_ACTIONS, costs=None, regime=None) -> float:
    """*Execution* (ADR-0049 §4): the winner's outcome less the passive outcome on the same box and
    side, averaged over the winner's trades. A market entry on a box *is* the passive trade on
    that box, so for one it is exactly nil and nothing is simulated; for a resting order it is
    what the order's fill added to, or took from, entering at the open."""
    records = list(records)
    if not records or compiled.spec.order_type.value == "market":
        return 0.0
    engine = _engine(compiled.engine)
    probes = {side: _market(compiled, compiled.spec.entries[0].__class__(EntryKind.ALWAYS, side, ())) for side in (Side.LONG, Side.SHORT)}
    boxes = {name: {day: (first, last) for day, first, last in bars.boxes()} for name, bars in bars_by_name.items()}
    kw = dict(cost_in_r=cost_in_r, actions=actions, costs=costs, regime=regime)
    diffs = []
    for t in records:
        first, last = boxes[t.name][t.day]
        bars = bars_by_name[t.name]
        passive_trade = (engine.simulate_position(probes[t.side], bars, first, **kw) if compiled.engine == POSITION_BOXED
                         else engine.simulate_box(probes[t.side], bars, first, last, **kw))
        if passive_trade is not None:
            diffs.append(t.net_r - passive_trade.net_r)
    return float(sum(diffs) / len(diffs)) if diffs else 0.0


def fifth_check(compiled: CompiledStrategy, bars_by_name: dict, records, baseline: Baseline, *, draws: int, seed: int,
                cost_in_r: float, actions: ActionSeries = _NO_ACTIONS, costs=None, regime=None):
    """(draws, the count they are means at, what a Measurement carries beside them) for the winner
    against its side-matched passive alternative — with the margin in its two parts."""
    cmp = against_passive(compiled, bars_by_name, records, baseline, draws=draws, seed=seed)
    execution = execution_part(compiled, bars_by_name, records, cost_in_r=cost_in_r, actions=actions, costs=costs, regime=regime)
    stats = cmp.stats() + (("long_share", baseline.share), ("selection", cmp.difference - execution), ("execution", execution))
    return cmp.draws, cmp.n, stats


def winner_stats(compiled: CompiledStrategy, bars_by_name: dict, records) -> tuple:
    """The winner's own dispersion, the standard error of its EV clustered by date, and its
    *effective* count — how many independent trades that standard error is worth, never more
    than it holds (ADR-0050 §4, ADR-0051 §2)."""
    records = list(records)
    values = [t.net_r for t in records]
    n = len(values)
    sd = float(np.std(values)) if n else 0.0
    _mean, se, block = inference.mean_by_day(calendar_of(bars_by_name), days=[t.day for t in records], values=values,
                                             hold=hold_of(compiled, records))
    n_eff = float(min(n, (sd / se) ** 2)) if se > 0 else float(n)
    return (("sd", sd), ("se_cluster", se), ("n_eff", n_eff), ("block", block))
