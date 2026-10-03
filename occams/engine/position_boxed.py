"""The position-boxed simulator (M9.1, F5, D6): the resampling unit is the
position. A position opens on a signal box and runs across bars until its
stop, its target, its time exit or the end of the data — so days are not
independent, and the null is drawn by **block bootstrap over positions in
time order** (M9.2), never by shuffling days (A5, H2).

Fills come from the vendored ``execution`` module as in the day-boxed
engine. A bar that opens through the stop fills at the open, and so does a
resting limit the bar opens through (ADR-0040); a split inside the hold
restates the stop first (M4.2). An entry the fill auditor refuses is a
missed trade: the position is not opened and the next signal is free to
(ADR-0041). A ``day_boxed`` compilation is
refused here and a ``position_boxed`` one is refused there (M9.3).
"""

from __future__ import annotations

from itertools import product
from collections.abc import Callable


from occams.core import execution as ex
from occams.costs.auditors import Fill, check_fill, family_of
from occams.engine.regime_gate import admits, check_gate
from occams.data.actions import ActionSeries, rebase
from occams.engine import probes
from occams.engine.common import cost as _cost, on_basis as _on_basis
from occams.engine.day_boxed import (NO_ACTIONS, Missed, TradeRecord, Trades, baseline_summary, limit_through_the_open,
                                     signal, stop_distance)
from occams.inference import block_bootstrap_means, block_length  # noqa: F401 — the names this module has always offered
from occams.data.bars import Bars
from occams.measurement import Cell, Measurement
from occams.sizing import r_multiple
from occams.spec.compile import CompiledStrategy, to_engine
from occams.spec.spec import ExitKind, Side, StrategySpec

NAME = "position_boxed"
ORDER_KIND = {"market": ex.MARKET, "limit": ex.LIMIT, "stop": ex.STOP, "stop_limit": ex.STOP}


class EngineRefusal(RuntimeError):
    pass


def _require_engine(compiled: CompiledStrategy) -> None:
    if compiled.engine != NAME:
        raise EngineRefusal(f"a {compiled.engine} compilation cannot run in the position-boxed simulator; "
                            f"horizon selects the simulator by type (D6)")


def simulate_position(compiled: CompiledStrategy, bars: Bars, first: int, *, cost_in_r: float,
                      actions: ActionSeries = NO_ACTIONS, costs=None, regime=None) -> TradeRecord | None:
    """One position from a signal at box ``first``, held across bars."""
    spec = compiled.spec
    if first == 0:
        return None
    if not admits(spec.regime, regime, bars, first):
        return None
    fired = None
    for entry in spec.entries:
        f, side, level = signal(entry, bars, first, actions)
        if f:
            fired = (side, level)
            break
    if fired is None:
        return None
    side, level = fired
    kind = ORDER_KIND[spec.order_type.value]
    order = ex.Order(kind, ex.BUY if side is Side.LONG else ex.SELL, None if kind == ex.MARKET else level)
    market = _on_basis(bars, first - 1, first, actions)[3]
    ex.validate(order, market)
    # the entry may fill on the signal bar only — a resting entry that never
    # fills that day is cancelled, so the position's box begins with its signal
    seg = slice(first - 1, first + 1)
    got = ex.fill(order, bars.high[seg], bars.low[seg], bars.open[seg], placed_at=0)
    if got is None:
        return None
    rel, entry_px = got
    ei = first - 1 + rel
    entry_px = limit_through_the_open(kind, side, level, entry_px, float(bars.open[ei]))
    dist = stop_distance(spec, bars, first, entry_px, actions)
    long = side is Side.LONG
    stop_lvl = entry_px - dist if long else entry_px + dist
    target = None
    time_bars = None
    for x in spec.exits:
        if x.kind is ExitKind.TARGET_R:
            m = x.param("multiple")
            target = entry_px + m * dist if long else entry_px - m * dist
        elif x.kind is ExitKind.TIME:
            time_bars = int(x.param("bars"))
    exit_px, xi, reason = None, None, None
    delist = actions.delisting(bars.name)
    for j in range(ei, bars.n):
        # restate the stop and target on bar j's basis: a split is not a breach
        s_j = rebase(stop_lvl, name=bars.name, from_day=bars.day[ei], to_day=bars.day[j], series=actions)
        t_j = None if target is None else rebase(target, name=bars.name, from_day=bars.day[ei], to_day=bars.day[j], series=actions)
        o, h, lo, c = bars.open[j], bars.high[j], bars.low[j], bars.close[j]
        if delist is not None and bars.day[j] >= delist.day:
            exit_px, xi, reason = float(delist.terms), j, "delisted"
            break
        if j > ei:
            gapped = o <= s_j if long else o >= s_j
            if gapped:
                exit_px, xi, reason = o, j, "gapped"
                break
        stopped = lo <= s_j if long else h >= s_j
        if stopped:
            exit_px, xi, reason = s_j, j, "stopped"
            break
        if t_j is not None and ((h >= t_j) if long else (lo <= t_j)):
            exit_px, xi, reason = t_j, j, "target"
            break
        if time_bars is not None and j - ei + 1 >= time_bars:
            exit_px, xi, reason = c, j, "time"
            break
    if exit_px is None:
        exit_px, xi, reason = bars.close[bars.n - 1], bars.n - 1, "data_end"
    # the R multiple is measured on the entry basis: restate the exit back
    exit_on_entry_basis = exit_px * actions.split_factor(bars.name, bars.day[ei], bars.day[xi]) \
        + actions.dividends_between(bars.name, bars.day[ei], bars.day[xi])
    gross = r_multiple(entry=entry_px, exit=exit_on_entry_basis, stop_distance=dist, side=side)
    cst = _cost(costs, cost_in_r, entry_px, dist)
    fill = Fill(price=float(entry_px), bar_index=ei, order_kind=kind, side=side,
                level=None if kind == ex.MARKET else float(level), prior_close=float(bars.close[ei - 1]),
                bar_open=float(bars.open[ei]), bar_high=float(bars.high[ei]), bar_low=float(bars.low[ei]),
                bar_volume=float(bars.volume[ei]), next_open=float(bars.open[ei + 1]) if ei + 1 < bars.n else None,
                name=bars.name, prior_day=bars.day[ei - 1], day=bars.day[ei])
    return TradeRecord(bars.name, bars.day[first], side, ei, xi, float(entry_px), float(exit_px), float(dist),
                       float(gross), float(gross - cst), reason, fill=fill, cost_in_r=float(cst))


def run(compiled: CompiledStrategy, bars_by_name: dict[str, Bars], *, seed: int, cost_in_r: float = 0.0,
        actions: ActionSeries = NO_ACTIONS, costs=None, audit_fills: bool = True, regime=None) -> Trades:
    """One position at a time per name: a new signal while a position is
    open is not taken (it would be the same bet). Deterministic. An entry
    the auditor refuses opens no position and is returned as ``missed``
    (ADR-0041)."""
    _require_engine(compiled)
    check_gate(compiled.spec.regime, regime)
    del seed
    family = family_of(compiled.spec) if audit_fills else None   # default-deny before a box runs (M5.7)
    out: list[TradeRecord] = []
    missed: list[Missed] = []
    for name in sorted(bars_by_name):
        bars = bars_by_name[name]
        busy_until = -1
        for _day, first, _last in bars.boxes():
            if first <= busy_until:
                continue
            t = simulate_position(compiled, bars, first, cost_in_r=cost_in_r, actions=actions, costs=costs, regime=regime)
            if t is None:
                continue
            why = check_fill(family, t.fill, actions) if audit_fills else ""
            if why:
                missed.append(Missed(t.name, t.day, t.entry_index, why))   # not opened: the next signal is free to
                continue
            out.append(t)
            busy_until = t.exit_index
    return Trades(out, missed)


# ---- the null: block bootstrap over positions in time order --------------

def _distribution(build, *args, **kwargs) -> tuple[float, ...]:
    try:
        return build(*args, **kwargs)
    except probes.ProbeRefusal as e:
        raise EngineRefusal(str(e)) from None


def null_distribution(compiled: CompiledStrategy, bars_by_name: dict[str, Bars], *, draws: int, seed: int,
                      cost_in_r: float, actions: ActionSeries = NO_ACTIONS, costs=None, regime=None) -> tuple[float, ...]:
    """Random entry, same stop and exits, positions in time order, block
    bootstrap over them. Sides are a seeded coin per box."""
    trades = probes.random_entry(compiled, bars_by_name, seed=seed, cost_in_r=cost_in_r, actions=actions, costs=costs, regime=regime)
    return _distribution(probes.random_entry_distribution, NAME, positions=trades, n_trades=len(trades), draws=draws, seed=seed)


def always_long_trades(compiled: CompiledStrategy, bars_by_name: dict[str, Bars], *, seed: int, cost_in_r: float,
                       actions: ActionSeries = NO_ACTIONS, costs=None, regime=None):
    """Always-long at this spec's geometry and gate — a market order on every
    box, long, the same exits, stop, horizon and regime gate (ADR-0043, ADR-0045)."""
    return probes.passive(compiled, bars_by_name, side=Side.LONG, seed=seed, cost_in_r=cost_in_r, actions=actions, costs=costs,
                          regime=regime)


def baseline_distribution_of(trades, *, draws: int, seed: int) -> tuple[float, ...]:
    """ADR-0043: always-long's positions in time order, block bootstrap over them."""
    return _distribution(probes.passive_distribution, NAME, trades, n_trades=len(trades), draws=draws, seed=seed)


def baseline_distribution(compiled: CompiledStrategy, bars_by_name: dict[str, Bars], *, draws: int, seed: int,
                          cost_in_r: float, actions: ActionSeries = NO_ACTIONS, costs=None, regime=None) -> tuple[float, ...]:
    return baseline_distribution_of(always_long_trades(compiled, bars_by_name, seed=seed, cost_in_r=cost_in_r, actions=actions,
                                                       costs=costs, regime=regime), draws=draws, seed=seed)


def measure(template: StrategySpec, axes: dict[str, list[float]],
            cell_spec: Callable[[StrategySpec, dict[str, float]], StrategySpec],
            bars_by_name: dict[str, Bars], *, seed: int, cost_in_r: float, null_draws: int,
            partition: str = "measurement", actions: ActionSeries = NO_ACTIONS,
            partition_bounds: tuple[int, int] | None = None,
            split: tuple[float, float, float] | None = None, costs=None, regime=None) -> Measurement:
    names = list(axes)
    years = max(b.days for b in bars_by_name.values()) / 252.0
    cells: list[Cell] = []
    compiled_by_idx: dict[tuple[int, ...], CompiledStrategy] = {}
    passive: dict[tuple[int, ...], object] = {}
    for idx in product(*(range(len(axes[a])) for a in names)):
        params = {a: float(axes[a][i]) for a, i in zip(names, idx, strict=True)}
        c = to_engine(cell_spec(template, params))
        trades = run(c, bars_by_name, seed=seed, cost_in_r=cost_in_r, actions=actions, costs=costs, regime=regime)
        probe = always_long_trades(c, bars_by_name, seed=seed, cost_in_r=cost_in_r, actions=actions, costs=costs, regime=regime)
        base_ev, base_by = baseline_summary(probe)                                                           # ADR-0045
        cells.append(Cell(tuple(idx), tuple(sorted(params.items())), tuple(t.as_trade() for t in trades),
                          spec_hash=c.spec_hash, baseline_ev=base_ev, baseline_by_group=base_by))
        compiled_by_idx[tuple(idx)] = c
        passive[tuple(idx)] = probe
    if not any(c.trades for c in cells):
        raise EngineRefusal("the sweep traded nothing in every cell — an instrument failure, never a verdict")
    winner = Measurement(spec_hash="", engine=NAME, engine_sha="", seed=seed, partition=partition, years=years,
                         cells=tuple(cells), null_ev=()).winner                                                 # the surface's winner
    null = null_distribution(compiled_by_idx[winner.indices], bars_by_name, draws=null_draws, seed=seed,
                             cost_in_r=cost_in_r, actions=actions, costs=costs, regime=regime)
    baseline = baseline_distribution_of(passive[winner.indices], draws=null_draws, seed=seed)                     # ADR-0043
    any_compiled = next(iter(compiled_by_idx.values()))
    return Measurement(spec_hash=template.hash, engine=NAME, engine_sha=any_compiled.engine_sha, seed=seed,
                       partition=partition, years=years, cells=tuple(cells), null_ev=null,
                       partition_bounds=partition_bounds, split=split,
                       cost_basis=(costs.basis if costs is not None else "declared"), baseline_ev=baseline)
