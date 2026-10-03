"""The probes: what a spec's geometry and gate yield with no entry rule at all (M16.9; the
review's F20). A *passive* probe is a market order on every box, one side; *random entry*
is every box with the side by a seeded coin. The guards' two Monte Carlo distributions —
beats-null's and the fifth check's — are built from these, and so is the survey's
readiness table; before this module each engine and the survey built its own.

Behaviour is as it was built: the day-boxed probes are audited for obtainability like any
other fill and the position-boxed ones are not; the day-boxed distributions resample
boxes independently at the winner's trade count and the position-boxed ones block-bootstrap
positions in time order at the probe's own count. ADR-0048 and ADR-0049 change what is
drawn (M16.14, M16.15) — here, once.
"""

from __future__ import annotations

import numpy as np

from occams import inference
from occams.data.actions import ActionSeries
from occams.spec.compile import CompiledStrategy, to_engine
from occams.spec.spec import EntryKind, Side

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


def random_entry(compiled: CompiledStrategy, bars_by_name: dict, *, seed: int, cost_in_r: float,
                 actions: ActionSeries = _NO_ACTIONS, costs=None, regime=None):
    """Every box, the side by a seeded coin, the same stop, exits and gate."""
    probe = _market(compiled, compiled.spec.entries[0].__class__(EntryKind.COIN_FLIP, Side.LONG, (("seed", seed),)))
    return _engine(compiled.engine).run(probe, bars_by_name, seed=seed, cost_in_r=cost_in_r, actions=actions, costs=costs,
                                        audit_fills=AUDITED[compiled.engine], regime=regime)


def _in_time_order(trades) -> np.ndarray:
    return np.asarray([t.net_r for t in sorted(trades, key=lambda t: (t.entry_index, t.name))], dtype=float)


def random_entry_distribution(engine: str, *, longs=(), shorts=(), positions=(), n_trades: int, draws: int, seed: int) -> tuple[float, ...]:
    """Beats-null's distribution. Day-boxed: the long and the short outcome of every box,
    ``n_trades`` drawn independently with a coin for the side. Position-boxed: the coin's
    own positions in time order, block-bootstrapped."""
    if engine == POSITION_BOXED:
        if not positions:
            raise ProbeRefusal("random entry produced no positions to bootstrap")
        x = _in_time_order(positions)
        return tuple(float(v) for v in inference.block_bootstrap_means(x, block=inference.block_length(x), draws=draws, seed=seed))
    longs, shorts = np.asarray(longs, dtype=float), np.asarray(shorts, dtype=float)
    if longs.size == 0:
        raise ProbeRefusal("no boxes to draw a null from")
    return inference.coin_sided_means(longs, shorts, n=n_trades, draws=draws, seed=seed)


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
