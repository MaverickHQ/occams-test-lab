"""The day-boxed simulator (M3.7, F5). One box per session; a trade opens
and closes inside its box, so days are independent and the Monte Carlo
over days is valid (D6, H2). The multi-day hold is the position-boxed
simulator's job (M9.1) and is refused here.

Fills come from the vendored ``execution`` module — an order is declared,
the fill is derived from what the market did, and an entry price is never
an input. A protective stop fills at its level, or at the open when a bar
opens through it, so a gap through the stop records worse than -1R (M3.8).
A resting limit the bar opens through fills at the open the same way
(ADR-0040): the rule lives here, in the engine that owns the fill's
signature, never in the vendored module. Every fill is audited for
obtainability and a refused entry is a missed trade, recorded and not
opened (ADR-0041).
Within one bar the order of events is unknown; where a stop and a target
both lie inside a bar's range the stop is taken — the simulator assumes the
worse case, never the better.

Results are multiples of PLANNED R (D5). Costs are a declared ``cost_in_r``
here; the bounded cost model arrives at M5 behind the same argument.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass
from itertools import product
from collections.abc import Callable

import numpy as np

from occams.core import execution as ex
from occams.costs.auditors import Fill, check_fill, family_of
from occams.engine import probes
from occams.engine.common import cost as _cost, on_basis as _on_basis
from occams.engine.regime_gate import admits, check_gate
from occams.data.actions import ActionSeries
from occams.data.bars import Bars
from occams.measurement import Cell, Measurement, Trade
from occams.sizing import r_multiple
from occams.spec.compile import CompiledStrategy, to_engine
from occams.spec.spec import EntryKind, ExitKind, Side, StopKind, StrategySpec

NAME = "day_boxed"
ORDER_KIND = {"market": ex.MARKET, "limit": ex.LIMIT, "stop": ex.STOP, "stop_limit": ex.STOP}


class EngineRefusal(RuntimeError):
    pass


@dataclass(frozen=True)
class TradeRecord:
    name: str
    day: int
    side: Side
    entry_index: int
    exit_index: int
    entry: float
    exit: float
    stop_distance: float
    gross_r: float
    net_r: float
    reason: str  # stopped | gapped | target | time | box_end | delisted
    fill: Fill | None = None  # the entry fill's signature (M5.6)
    cost_in_r: float = 0.0

    def as_trade(self) -> Trade:
        return Trade(self.net_r, self.name, self.day)


@dataclass(frozen=True)
class Missed:
    """An entry the fill auditor refused: the position is not opened, and
    the record says which bar and why (ADR-0041)."""

    name: str
    day: int
    bar_index: int
    reason: str


class Trades(tuple):
    """The trades a run kept — a tuple, as every caller reads it — carrying
    the entries the auditor refused as ``missed`` (ADR-0041)."""

    missed: tuple[Missed, ...]

    def __new__(cls, trades=(), missed=()):
        self = super().__new__(cls, trades)
        self.missed = tuple(missed)
        return self


# ---- signals: computed from bars strictly before the box ----------------

NO_ACTIONS = ActionSeries()


def _atr(bars: Bars, end: int, lookback: int, actions: ActionSeries = NO_ACTIONS) -> float:
    """Average true range over bars [end-lookback, end), on ``end``'s basis."""
    trs = []
    for i in range(max(1, end - lookback), end):
        _, h, lo, _c = _on_basis(bars, i, end, actions)
        _, _, _, pc = _on_basis(bars, i - 1, end, actions)
        trs.append(max(h - lo, abs(h - pc), abs(lo - pc)))
    if not trs:
        _, h, lo, _ = _on_basis(bars, end - 1, end, actions)
        return h - lo
    return float(sum(trs) / len(trs))


def _coin(seed: int, name: str, day: int) -> Side:
    rng = np.random.default_rng([int(seed), zlib.crc32(name.encode("utf-8")), int(day)])
    return Side.LONG if rng.random() < 0.5 else Side.SHORT


def signal(entry, bars: Bars, first: int, actions: ActionSeries = NO_ACTIONS) -> tuple[bool, Side, float | None]:
    """(fires, side, level) using bars [0, first) only — never the box itself.
    Prior bars are read on the box's basis, so a split loads as an action."""
    k = entry.kind
    if k is EntryKind.ALWAYS:
        return True, entry.side, None
    if k is EntryKind.COIN_FLIP:
        return True, _coin(int(entry.param("seed")), bars.name, bars.day[first]), None
    if k is EntryKind.DOWN_RUN:                      # ADR-0037: each of the last `runs` closes lower than the one before
        runs = int(entry.param("runs"))
        if runs < 1 or first < runs + 1:
            return False, entry.side, None
        closes = [_on_basis(bars, i, first, actions)[3] for i in range(first - runs - 1, first)]
        return all(b < a for a, b in zip(closes, closes[1:], strict=False)), entry.side, None
    if k is EntryKind.RETURN_BELOW:                  # ADR-0037: a decline of a declared size over a declared window
        lb, pct = int(entry.param("lookback")), float(entry.param("percent"))
        if lb < 1 or first < lb + 1:
            return False, entry.side, None
        then = _on_basis(bars, first - 1 - lb, first, actions)[3]
        prev = _on_basis(bars, first - 1, first, actions)[3]
        return (prev / then - 1.0) <= -pct / 100.0, entry.side, None
    if k is EntryKind.PULLBACK_IN_TREND:             # ADR-0037: below the short average, above the long one
        short, long = int(entry.param("short")), int(entry.param("long"))
        if short < 1 or short >= long or first < long:
            return False, entry.side, None
        closes = [_on_basis(bars, i, first, actions)[3] for i in range(first - long, first)]
        ma_long = sum(closes) / long
        ma_short = sum(closes[-short:]) / short
        prev = closes[-1]
        return (prev < ma_short) and (prev > ma_long), entry.side, None
    lb = int(entry.param("lookback"))
    if first < lb or lb < 1:
        return False, entry.side, None
    window = range(first - lb, first)
    rows = [_on_basis(bars, i, first, actions) for i in window]
    if k is EntryKind.BREAKOUT_HIGH:
        return True, entry.side, max(r[1] for r in rows)
    if k is EntryKind.BREAKOUT_LOW:
        return True, entry.side, min(r[2] for r in rows)
    ma = sum(r[3] for r in rows) / lb
    prev = rows[-1][3]
    if k is EntryKind.CLOSE_ABOVE_MA:
        return prev > ma, entry.side, None
    if k is EntryKind.CLOSE_BELOW_MA:
        return prev < ma, entry.side, None
    raise EngineRefusal(f"unknown entry kind {k}")


def stop_distance(spec: StrategySpec, bars: Bars, first: int, entry_price: float,
                  actions: ActionSeries = NO_ACTIONS) -> float:
    if spec.stop.kind is StopKind.PERCENT:
        return entry_price * spec.stop.value / 100.0
    return spec.stop.value * _atr(bars, first, spec.stop.lookback, actions)


# ---- one box ------------------------------------------------------------

def limit_through_the_open(kind: str, side: Side, level, entry_px: float, bar_open: float) -> float:
    """ADR-0040: a resting limit that the bar opens through fills at the open
    — a buy limit at min(open, level), a sell limit at max(open, level) — the
    mirror of the stop rule the vendored module already applies (M3.8). Any
    other order, or a limit the bar reached from the right side, is unchanged."""
    if kind != ex.LIMIT or level is None:
        return entry_px
    if side is Side.LONG and bar_open < level:
        return bar_open
    if side is Side.SHORT and bar_open > level:
        return bar_open
    return entry_px


def simulate_box(compiled: CompiledStrategy, bars: Bars, first: int, last: int, *,
                 cost_in_r: float, actions: ActionSeries = NO_ACTIONS, costs=None, regime=None) -> TradeRecord | None:
    spec = compiled.spec
    if first == 0:
        return None  # nothing known before the first bar
    if not admits(spec.regime, regime, bars, first):
        return None  # the frozen classifier says this box is not in the Strategy's regime
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
    market = _on_basis(bars, first - 1, first, actions)[3]  # prior close on the box's basis
    ex.validate(order, market)  # raises Unplaceable: the per-bar A4 guard
    seg = slice(first - 1, last + 1)
    got = ex.fill(order, bars.high[seg], bars.low[seg], bars.open[seg], placed_at=0)
    if got is None:
        return None
    rel, entry_px = got
    ei = first - 1 + rel
    entry_px = limit_through_the_open(kind, side, level, entry_px, float(bars.open[ei]))
    dist = stop_distance(spec, bars, first, entry_px, actions)
    if dist <= 0:
        raise EngineRefusal("stop distance collapsed to zero")
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
    for j in range(ei, last + 1):
        o, h, lo, c = bars.open[j], bars.high[j], bars.low[j], bars.close[j]
        if j > ei:
            gapped = o <= stop_lvl if long else o >= stop_lvl
            if gapped:
                exit_px, xi, reason = o, j, "gapped"
                break
        stopped = lo <= stop_lvl if long else h >= stop_lvl
        if stopped:
            exit_px, xi, reason = stop_lvl, j, "stopped"
            break
        if target is not None and ((h >= target) if long else (lo <= target)):
            exit_px, xi, reason = target, j, "target"
            break
        if time_bars is not None and j - ei + 1 >= time_bars:
            exit_px, xi, reason = c, j, "time"
            break
    delisting = actions.delisting(bars.name)
    if delisting is not None and delisting.day == bars.day[first] and reason in (None, "time", "box_end"):
        exit_px, xi, reason = float(delisting.terms), last, "delisted"  # a vanishing name exits on its terms (M4.3)
    if exit_px is None:
        exit_px, xi, reason = bars.close[last], last, "box_end"
    gross = r_multiple(entry=entry_px, exit=exit_px, stop_distance=dist, side=side)
    c = _cost(costs, cost_in_r, entry_px, dist)
    fill = Fill(price=float(entry_px), bar_index=ei, order_kind=kind, side=side,
                level=None if kind == ex.MARKET else float(level), prior_close=float(bars.close[ei - 1]),
                bar_open=float(bars.open[ei]), bar_high=float(bars.high[ei]), bar_low=float(bars.low[ei]),
                bar_volume=float(bars.volume[ei]), next_open=float(bars.open[ei + 1]) if ei + 1 < bars.n else None,
                name=bars.name, prior_day=bars.day[ei - 1], day=bars.day[ei])
    return TradeRecord(bars.name, bars.day[first], side, ei, xi, float(entry_px), float(exit_px),
                       float(dist), float(gross), float(gross - c), reason, fill=fill, cost_in_r=float(c))


def run(compiled: CompiledStrategy, bars_by_name: dict[str, Bars], *, seed: int,
        cost_in_r: float = 0.0, actions: ActionSeries = NO_ACTIONS, costs=None,
        audit_fills: bool = True, regime=None) -> Trades:
    """Deterministic for (spec, seed, bars, actions, costs). ``seed`` reaches
    only the apparatus entries that declare one; a deterministic rule
    ignores it. Every fill is audited for obtainability before it counts
    (M5.5): a refused entry is not opened and is returned as ``missed``
    (ADR-0041); ``costs`` is the equity cost model, else a declared ``cost_in_r``."""
    if compiled.engine != NAME:
        raise EngineRefusal(f"a {compiled.engine} compilation cannot run in the day-boxed simulator: a multi-day "
                            f"hold through a Monte Carlo that assumes independent days is the A5 failure (D6, M9.3)")
    check_gate(compiled.spec.regime, regime)
    del seed  # rules are pure functions of the bars; the coin declares its own seed
    family = family_of(compiled.spec) if audit_fills else None   # default-deny before a box runs (M5.7)
    out: list[TradeRecord] = []
    missed: list[Missed] = []
    for name in sorted(bars_by_name):
        bars = bars_by_name[name]
        for _day, first, last in bars.boxes():
            t = simulate_box(compiled, bars, first, last, cost_in_r=cost_in_r, actions=actions, costs=costs, regime=regime)
            if t is None:
                continue
            why = check_fill(family, t.fill, actions) if audit_fills else ""
            if why:
                missed.append(Missed(t.name, t.day, t.entry_index, why))
            else:
                out.append(t)
    return Trades(out, missed)


# ---- the null: random entry, same costs and geometry --------------------

def box_outcomes(compiled: CompiledStrategy, bars_by_name: dict[str, Bars], *, cost_in_r: float,
                 actions: ActionSeries = NO_ACTIONS, costs=None, regime=None) -> tuple[np.ndarray, np.ndarray]:
    """Net R for a market entry at each box's open, long and short, under
    this spec's stop and exits — the geometry random entry is measured
    against. The regime gate is part of the geometry: random entry is drawn
    from the same gated boxes, so the null isolates the entry rule's
    contribution within the regime rather than crediting the regime's own
    drift to the Strategy."""
    longs, shorts = (probes.passive(compiled, bars_by_name, side=side, cost_in_r=cost_in_r, actions=actions, costs=costs, regime=regime)
                     for side in (Side.LONG, Side.SHORT))
    return np.asarray([t.net_r for t in longs], dtype=float), np.asarray([t.net_r for t in shorts], dtype=float)


def _distribution(build, *args, **kwargs) -> tuple[float, ...]:
    try:
        return build(*args, **kwargs)
    except probes.ProbeRefusal as e:
        raise EngineRefusal(str(e)) from None


def always_long_trades(compiled: CompiledStrategy, bars_by_name: dict[str, Bars], *, seed: int, cost_in_r: float,
                       actions: ActionSeries = NO_ACTIONS, costs=None, regime=None):
    """Always-long at this spec's geometry and gate: a market order on every box, long (ADR-0045)."""
    return probes.passive(compiled, bars_by_name, side=Side.LONG, seed=seed, cost_in_r=cost_in_r, actions=actions, costs=costs,
                          regime=regime)


def baseline_summary(trades) -> tuple[float | None, tuple[tuple[str, float, int], ...]]:
    """Always-long's EV, pooled and per group, from its trades."""
    by: dict[str, list[float]] = {}
    for t in trades:
        by.setdefault(t.name, []).append(t.net_r)
    if not by:
        return None, ()
    pooled = sum(v for vs in by.values() for v in vs) / sum(len(vs) for vs in by.values())
    return pooled, tuple((g, sum(vs) / len(vs), len(vs)) for g, vs in sorted(by.items()))


# ---- the sweep -> Measurement -------------------------------------------

def measure(template: StrategySpec, axes: dict[str, list[float]],
            cell_spec: Callable[[StrategySpec, dict[str, float]], StrategySpec],
            bars_by_name: dict[str, Bars], *, seed: int, cost_in_r: float, null_draws: int,
            partition: str = "measurement", actions: ActionSeries = NO_ACTIONS,
            partition_bounds: tuple[int, int] | None = None,
            split: tuple[float, float, float] | None = None, costs=None, regime=None) -> Measurement:
    """Compile and run one spec per cell of the declared sweep; the null is
    drawn under the winner's geometry at the winner's trade count, by
    calendar day (ADR-0048). The partition and its bounds are stamped into
    the result (M4.6)."""
    names = list(axes)
    years = max(b.days for b in bars_by_name.values()) / 252.0
    cells: list[Cell] = []
    compiled_by_idx: dict[tuple[int, ...], CompiledStrategy] = {}
    passive: dict[tuple[int, ...], Trades] = {}
    for idx in product(*(range(len(axes[a])) for a in names)):
        params = {a: float(axes[a][i]) for a, i in zip(names, idx, strict=True)}
        c = to_engine(cell_spec(template, params))
        trades = run(c, bars_by_name, seed=seed, cost_in_r=cost_in_r, actions=actions, costs=costs, regime=regime)
        passive[tuple(idx)] = always_long_trades(c, bars_by_name, seed=seed, cost_in_r=cost_in_r, actions=actions, costs=costs,
                                                 regime=regime)
        base_ev, base_by = baseline_summary(passive[tuple(idx)])                                                # ADR-0045
        cells.append(Cell(tuple(idx), tuple(sorted(params.items())), tuple(t.as_trade() for t in trades),
                          spec_hash=c.spec_hash, baseline_ev=base_ev, baseline_by_group=base_by))
        compiled_by_idx[tuple(idx)] = c
    if not any(c.trades for c in cells):
        raise EngineRefusal("the sweep traded nothing in every cell — an instrument failure, never a verdict")
    winner = Measurement(spec_hash="", engine=NAME, engine_sha="", seed=seed, partition=partition, years=years,
                         cells=tuple(cells), null_ev=()).winner                                                 # the surface's winner
    longs = passive[winner.indices]
    shorts = probes.passive(compiled_by_idx[winner.indices], bars_by_name, side=Side.SHORT, cost_in_r=cost_in_r, actions=actions,
                            costs=costs, regime=regime)
    n = max(winner.n, 1)
    against = _distribution(probes.against_random_entry, compiled_by_idx[winner.indices], bars_by_name, winner.trades, longs=longs,
                            shorts=shorts, draws=null_draws, seed=seed)                                         # ADR-0048
    baseline = _distribution(probes.passive_distribution, NAME, longs, n_trades=n, draws=null_draws, seed=seed)   # ADR-0043
    any_compiled = next(iter(compiled_by_idx.values()))
    return Measurement(spec_hash=template.hash, engine=NAME, engine_sha=any_compiled.engine_sha, seed=seed,
                       partition=partition, years=years, cells=tuple(cells), null_ev=against.draws,
                       partition_bounds=partition_bounds, split=split,
                       cost_basis=(costs.basis if costs is not None else "declared"), baseline_ev=baseline,
                       null_n=against.n, null_stats=against.stats(), baseline_n=n)
