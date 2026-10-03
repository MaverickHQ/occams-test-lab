"""The size-and-power table (M16.7; ADR-0047 §6; the review's F23).

`make null` shows that a coin flip is refused once. It does not show how often a
guard errs: on the null control the floor alone refuses the coin flip, so the
Monte Carlo guards' false-positive rates were never measured — which is how a
position-boxed null at fourteen times its declared rate, and a fifth check a coin
flip can pass, shipped. This module runs each Monte Carlo guard **in isolation**,
over many seeds, on worlds whose truth is known, and reports the rate at which it
refuses or passes against the rate it declares.

A row is within tolerance when its measured size is at most
``alpha + 2.33 * sqrt(alpha * (1 - alpha) / seeds)``, or its measured power at
least ``planned - 2.33 * sqrt(p * (1 - p) / seeds)``. The worlds are apparatus,
not the author's: no number here is a floor, an alpha budget or a falsifier.

    python -m occams.calibrate [--save FILE] [--strict]   # print the table (`make calibrate`)
    python -m pytest -m calibration                       # the same rows as tests, never part of `make check`
"""

from __future__ import annotations

import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

import numpy as np

from occams.config import InformationAxis
from occams.data.bars import Bars
from occams.inference import guard_p, monte_carlo_p
from occams.spec import (Capability, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType, Side, Sizing, Stop,
                         StopKind, StrategySpec, UniverseRule)

ALPHAS = (0.01, 0.05)
SIZE_SEEDS = 200          # the review's S for a size; ADR-0047 §6 asks for at least this many
POWER_SEEDS = 100
Z_TOLERANCE = 2.33
DRAWS = 2000              # resolves alpha 0.01 at twenty expected exceedances, as the guards require


def size_tolerance(alpha: float, seeds: int) -> float:
    """The largest measured size that is still the declared alpha, at ``seeds`` seeds."""
    return alpha + Z_TOLERANCE * math.sqrt(alpha * (1.0 - alpha) / seeds)


def power_tolerance(planned: float, seeds: int) -> float:
    """The smallest measured power that is still the planned power, at ``seeds`` seeds."""
    return planned - Z_TOLERANCE * math.sqrt(planned * (1.0 - planned) / seeds)


def common_factor_world(seed: int, *, names: int, days: int = 1260, sigma: float = 0.02, rho: float = 0.0,
                        drift: float | None = None) -> dict[str, Bars]:
    """Daily bars for ``names`` instruments whose log returns share a market factor with
    correlation ``rho``. With ``drift`` left at ``-sigma^2 / 2`` every price is a martingale:
    no entry, on any side, has an expectation other than nil before costs."""
    rng = np.random.default_rng([int(seed), 99])
    zc = rng.standard_normal(days)
    mu = -sigma ** 2 / 2 if drift is None else float(drift)
    out: dict[str, Bars] = {}
    for i in range(names):
        zi = rng.standard_normal(days)
        r = mu + sigma * (math.sqrt(rho) * zc + math.sqrt(1.0 - rho) * zi)
        closes = 100.0 * np.exp(np.cumsum(r))
        opens = np.concatenate(([100.0], closes[:-1]))
        span = np.abs(closes - opens) * 0.5 + 100.0 * sigma * 0.25 * rng.random(days)
        name = f"N{i:02d}"
        out[name] = Bars(name, tuple(map(float, opens)), tuple(map(float, np.maximum(opens, closes) + span)),
                         tuple(map(float, np.minimum(opens, closes) - span)), tuple(map(float, closes)),
                         tuple([1e6] * days), tuple(range(days)))
    return out


def _spec(entry: Entry, *, horizon: Horizon, hold: int, stop_percent: float) -> StrategySpec:
    return StrategySpec(entries=(entry,), exits=(Exit(ExitKind.TIME, (("bars", hold),)),), stop=Stop(StopKind.PERCENT, stop_percent),
                        sizing=Sizing(), order_type=OrderType.MARKET, horizon=horizon,
                        universe=UniverseRule((("world", "calibration"),)),
                        required_capabilities=frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS}),
                        axis=InformationAxis.PRICE_DAILY)


def _down_run(runs: int) -> Entry:
    """Long after ``runs`` lower closes: an entry with no skill on a martingale, and on a
    drifting market none beyond being long."""
    return Entry(EntryKind.DOWN_RUN, Side.LONG, (("runs", runs),))


@dataclass(frozen=True)
class Row:
    """One line of the table: a guard, in isolation, on a world whose truth is known."""

    key: str
    engine: str
    world: str
    guard: str            # "beats_null" | "beats_always_long"
    kind: str             # "size": the guard should fire at most at alpha · "power": at least at `planned`
    seeds: int
    planned: float = 0.0
    fixed_by: str = ""    # the M16 row that brings a known failure inside tolerance; "" when none is known


DOWN_DRIFT = -0.001       # log return a day: a market that falls, so being long loses and a coin's short half gains
FAR_STOP = 60.0           # per cent: thirteen standard deviations of a five-day move, so it never binds and long mirrors short exactly
UP_DRIFT = 0.0005


def _measure(world: str, seed: int):
    """The Measurement a probe's world yields at one seed — through the shipped engine, untouched.
    ``world`` is ``engine:paths[:entry]``; the entry is a down-run unless it says ``coin``."""
    from occams.engine import day_boxed, position_boxed

    engine, paths, *entry = world.split(":")
    rho = 0.5 if "rho0.5" in paths else 0.0
    drift = DOWN_DRIFT if "downdrift" in paths else UP_DRIFT if "updrift" in paths else None
    coin = Entry(EntryKind.COIN_FLIP, Side.LONG, (("seed", seed),)) if entry == ["coin"] else None
    if engine == "position_boxed":
        bars = common_factor_world(seed, names=8, rho=rho, drift=drift)
        spec = _spec(coin or _down_run(3), horizon=Horizon.MULTI_DAY, hold=5, stop_percent=FAR_STOP if "farstop" in paths else 10.0)
        return position_boxed.measure(spec, {"hold": [5.0]}, lambda t, p: t, bars, seed=seed, cost_in_r=0.0, null_draws=DRAWS)
    bars = common_factor_world(seed, names=10, rho=rho, drift=drift)
    spec = _spec(coin or _down_run(2), horizon=Horizon.INTRADAY, hold=1, stop_percent=5.0)
    return day_boxed.measure(spec, {"hold": [1.0]}, lambda t, p: t, bars, seed=seed, cost_in_r=0.0, null_draws=DRAWS)


def p_values(task: tuple[str, int]) -> tuple[float, float]:
    """(p of beats-null, p of beats-always-long) for one world at one seed. Top-level, so a
    process pool can run it."""
    world, seed = task
    m = _measure(world, seed)
    w = m.winner
    # beats-null acts on the larger of its two p-values (ADR-0048 §5); the fifth check on its bootstrap's until M16.15
    return guard_p(monte_carlo_p(m.null_ev, w.ev), m.null_stats, w), monte_carlo_p(m.baseline_ev, w.ev)


RESIDUAL = "an open residual at 0.05: ADR-0048, as built"

ROWS: tuple[Row, ...] = (
    # beats-null: an entry with no skill on a martingale must pass at most at alpha
    Row("day_boxed:martingale-rho0.0", "day_boxed", "a martingale, independent names", "beats_null", "size", SIZE_SEEDS),
    Row("day_boxed:martingale-rho0.5", "day_boxed", "a martingale, names sharing a market (rho 0.5)", "beats_null", "size", SIZE_SEEDS),
    Row("position_boxed:martingale-rho0.0", "position_boxed", "a martingale, independent names", "beats_null", "size", SIZE_SEEDS),
    # the multi-day engine on a shared market: at its declared rate at 0.01, on the edge of tolerance at 0.05 (ADR-0048, as built)
    Row("position_boxed:martingale-rho0.5-farstop", "position_boxed", "a martingale, names sharing a market, a stop too far to bind",
        "beats_null", "size", SIZE_SEEDS, fixed_by=RESIDUAL),
    Row("position_boxed:martingale-rho0.5", "position_boxed", "a martingale, names sharing a market, a stop that binds", "beats_null", "size",
        SIZE_SEEDS, fixed_by=RESIDUAL),
    # beats-always-long: an entry that adds nothing over the passive alternative must pass at most at alpha
    Row("day_boxed:updrift-rho0.5", "day_boxed", "an upward drift, names sharing a market; long with no timing skill",
        "beats_always_long", "size", SIZE_SEEDS),
    Row("position_boxed:martingale-rho0.0", "position_boxed", "a martingale, independent names; long with no skill",
        "beats_always_long", "size", SIZE_SEEDS, fixed_by="M16.15"),
    Row("day_boxed:downdrift-rho0.0:coin", "day_boxed", "a downward drift, entered by a coin flip: its short half is not skill",
        "beats_always_long", "size", SIZE_SEEDS, fixed_by="M16.15"),
)


def row(world_key: str, guard: str) -> Row:
    return next(r for r in ROWS if r.key == world_key and r.guard == guard)


def _workers() -> int:
    return max(1, min(8, (os.cpu_count() or 2)))


_CACHE: dict[tuple[str, int], tuple[tuple[float, float], ...]] = {}
SAVED = "OCCAMS_CALIBRATION_CACHE"      # a file `--save` wrote: the tests read the table's p-values instead of drawing them twice


def _code_stamp() -> str:
    """The engine code the p-values were drawn on; a saved table from other code is not read."""
    from occams import identity

    return identity.own_code_sha()


def _saved() -> dict:
    path = os.environ.get(SAVED, "")
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as f:
        blob = json.load(f)
    return blob.get("worlds", {}) if blob.get("code") == _code_stamp() else {}


def collect(world: str, seeds: int) -> tuple[tuple[float, float], ...]:
    """Every seed's pair of p-values for one world, computed once per process and shared by
    the rows that read the same world."""
    key = (world, seeds)
    if key not in _CACHE:
        saved = _saved().get(f"{world}|{seeds}")
        if saved is not None:
            _CACHE[key] = tuple((float(a), float(b)) for a, b in saved)
        else:
            tasks = [(world, s) for s in range(1, seeds + 1)]
            with ProcessPoolExecutor(max_workers=_workers()) as pool:
                _CACHE[key] = tuple(pool.map(p_values, tasks, chunksize=4))
    return _CACHE[key]


def save(path: str) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"code": _code_stamp(), "worlds": {f"{w}|{n}": [list(p) for p in ps] for (w, n), ps in _CACHE.items()}}, f)


def rate(row: Row, alpha: float) -> float:
    """How often the guard lets the world through at ``alpha``: for a size row, the false-positive rate."""
    col = 0 if row.guard == "beats_null" else 1
    ps = [p[col] for p in collect(row.key, row.seeds)]
    return sum(1 for p in ps if p <= alpha) / len(ps)


def within(row: Row, alpha: float) -> tuple[bool, float, float]:
    """(within tolerance?, measured, the bound) for one row at one alpha."""
    got = rate(row, alpha)
    if row.kind == "size":
        bound = size_tolerance(alpha, row.seeds)
        return got <= bound, got, bound
    bound = power_tolerance(row.planned, row.seeds)
    return got >= bound, got, bound


def table() -> list[dict]:
    out = []
    for row in ROWS:
        for alpha in ALPHAS:
            ok, got, bound = within(row, alpha)
            out.append({"engine": row.engine, "guard": row.guard, "world": row.world, "kind": row.kind, "alpha": alpha,
                        "measured": got, "bound": bound, "within": ok, "seeds": row.seeds, "fixed_by": row.fixed_by})
    return out


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    strict = "--strict" in argv
    rows = table()
    print("The size-and-power table (ADR-0047 §6): each Monte Carlo guard in isolation, on a world whose truth is known.")
    print(f"{'engine':15s} {'guard':18s} {'alpha':>5s} {'measured':>8s} {'bound':>6s}  {'':6s} world")
    out_of = 0
    for r in rows:
        mark = "ok" if r["within"] else "OVER" if r["kind"] == "size" else "UNDER"
        known = r["fixed_by"]
        note = "" if r["within"] or not known else f"  ({known})" if known == RESIDUAL else f"  (a known defect: {known} fixes it)"
        out_of += 0 if r["within"] else 1
        print(f"{r['engine']:15s} {r['guard']:18s} {r['alpha']:5.2f} {r['measured']:8.3f} {r['bound']:6.3f}  {mark:6s} "
              f"{r['world']} [{r['seeds']} seeds]{note}")
    print(f"{len(rows) - out_of} of {len(rows)} rows within tolerance.")
    if "--save" in argv:
        save(argv[argv.index("--save") + 1])
    return 1 if (strict and out_of) else 0


if __name__ == "__main__":
    raise SystemExit(main())
