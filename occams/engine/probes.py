"""The probes: what a spec's geometry and gate yield with no entry rule at all (M16.9; the
review's F20). A *passive* probe is a market order on every box, one side. The guards' two
Monte Carlo distributions — beats-null's and the fifth check's — are built from these, and
so is the survey's readiness table; before this module each engine and the survey built
its own.

Beats-null (M16.14, ADR-0048): the winner against random entry — a coin's side on every box,
which is half the long passive outcome and half the short — summed by calendar day and
resampled together in blocks of days, at the winner's count.

The fifth check is as it was built until M16.15 (ADR-0049): the day-boxed distribution
resamples always-long's boxes independently at the winner's trade count and the
position-boxed one block-bootstraps its positions in time order at the probe's own count.
The day-boxed probes are audited for obtainability like any other fill and the
position-boxed ones are not, as built.
"""

from __future__ import annotations

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


def _in_time_order(trades) -> np.ndarray:
    return np.asarray([t.net_r for t in sorted(trades, key=lambda t: (t.entry_index, t.name))], dtype=float)


def passive_distribution(engine: str, trades, *, n_trades: int, draws: int, seed: int) -> tuple[float, ...]:
    """The fifth check's distribution (ADR-0043): always-long's outcomes at the same geometry
    and gate. Day-boxed: ``n_trades`` drawn independently. Position-boxed: its positions in
    time order, block-bootstrapped."""
    if engine == POSITION_BOXED:
        if not trades:
            raise ProbeRefusal("always-long produced no positions to bootstrap")
        x = _in_time_order(trades)
        return tuple(float(v) for v in inference.block_bootstrap_means(x, block=inference.block_length(x), draws=draws, seed=int(seed) + 11))
    longs = np.asarray([t.net_r for t in trades], dtype=float)
    if longs.size == 0:
        raise ProbeRefusal("no boxes to draw an always-long baseline from")
    return inference.resampled_means(longs, n=n_trades, draws=draws, seed=seed)
