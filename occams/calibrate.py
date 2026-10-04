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
from occams.inference import guard_p, monte_carlo_p, one_sided_n, one_sided_p
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
    guard: str            # one of GUARDS
    kind: str             # "size": the guard should fire at most at alpha · "power": at least at `planned`
    seeds: int
    planned: float = 0.0
    fixed_by: str = ""    # the M16 row that brings a known failure inside tolerance; "" when none is known
    alpha: float | None = None   # a power row is read at the alpha its guard runs at; a size row at each of ALPHAS

    @property
    def alphas(self) -> tuple[float, ...]:
        return ALPHAS if self.alpha is None else (self.alpha,)


DOWN_DRIFT = -0.001       # log return a day: a market that falls, so being long loses and a coin's short half gains
FAR_STOP = 60.0           # per cent: thirteen standard deviations of a five-day move, so it never binds and long mirrors short exactly
UP_DRIFT = 0.0005


def _measure(world: str, seed: int):
    """The Measurement a probe's world yields at one seed — through the shipped engine, untouched.
    ``world`` is ``engine:paths[:entry]``; the entry is a down-run unless it says ``coin``."""
    from occams.engine import day_boxed, position_boxed

    engine, paths, *entry = world.split(":")
    if engine.startswith("controls"):             # a control's own world, through the control's own sweep
        from occams.controls import _day_boxed_measurement, load_controls, synthetic_measurement

        if engine == "controls-synthetic":
            return synthetic_measurement(paths, load_controls(), seed)
        return _day_boxed_measurement(paths, load_controls(), seed, None, None, None)[1]
    if engine == "synthetic":                     # one cell of the law, its true EV at the floor or at the alternative
        at_floor = paths == "at-floor"
        per_group = 200 if at_floor else -(-one_sided_n(SIGMA, ALTERNATIVE - FLOOR, alpha=0.01, power=0.80) // 5)
        return _law(seed, ev=FLOOR if at_floor else ALTERNATIVE, per_group=per_group)
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


GUARDS = ("beats_null", "beats_always_long", "clears_floor", "all_five")
FLOOR, ALTERNATIVE, SIGMA = 0.15, 0.30, 1.2      # the synthetic law's floor, alternative and dispersion: apparatus, as in controls.toml


def _law(seed: int, *, ev: float, per_group: int):
    """One cell of the synthetic law whose true EV, net of its spread, is ``ev``."""
    from occams.engine import synthetic

    return synthetic.measure(spec_hash="calibration", seed=seed, axes={"stop": [1.0]}, groups=list("ABCDE"), years=1.0,
                             trades_per_group_year=float(per_group), sigma_r=SIGMA, cost_in_r=0.05, effect=synthetic.flat(ev + 0.05),
                             null_draws=DRAWS)


def _control(world: str):
    """(the control's kind, its engine, its Hypothesis) for a ``controls:`` or ``controls-synthetic:`` world."""
    from occams.controls import hypothesis, load_controls

    engine, kind = world.split(":")[:2]
    name = "day_boxed" if engine == "controls" else "synthetic"
    return kind, name, hypothesis(kind, load_controls(), engine=name)


def p_values(task: tuple[str, int]) -> tuple[float, float, float, float]:
    """One world at one seed, as the p each guard acts on — in the order of ``GUARDS``. Top-level, so a process pool
    can run it. A guard a world does not exercise reads 1.0: it lets nothing through."""
    from occams.guards import forward

    world, seed = task
    m = _measure(world, seed)
    w = m.winner
    # each Monte Carlo guard acts on the larger of its two p-values: the bootstrap's and the clustered standard error's (ADR-0048 §5)
    p_null = guard_p(monte_carlo_p(m.null_ev, w.ev), m.null_stats, w)
    p_base = guard_p(monte_carlo_p(m.baseline_ev, w.ev), m.baseline_stats, w)
    p_floor, p_all = 1.0, 1.0
    if world.startswith("synthetic:"):
        # the bound at alpha clears the floor exactly when the one-sided p of (EV - floor) / se is at most alpha (ADR-0050)
        p_floor = one_sided_p((w.ev - FLOOR) / dict(m.winner_stats)["se_cluster"])
    elif world.startswith("controls"):
        p_all = 0.0 if forward.check(m, _control(world)[2]) is None else 1.0       # accepted by all five, at the control's own alphas
    return p_null, p_base, p_floor, p_all


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
    # the fifth check: an entry that adds nothing over the passive alternative at its own side mix must pass at most at alpha
    Row("day_boxed:updrift-rho0.5", "day_boxed", "an upward drift, names sharing a market; long with no timing skill",
        "beats_always_long", "size", SIZE_SEEDS),
    Row("position_boxed:martingale-rho0.0", "position_boxed", "a martingale, independent names; long with no skill",
        "beats_always_long", "size", SIZE_SEEDS),
    Row("position_boxed:martingale-rho0.5", "position_boxed", "a martingale, names sharing a market, a stop that binds; long with no skill",
        "beats_always_long", "size", SIZE_SEEDS),
    Row("day_boxed:downdrift-rho0.0:coin", "day_boxed", "a downward drift, entered by a coin flip: its short half is not skill",
        "beats_always_long", "size", SIZE_SEEDS),
    # and it must still see what is there: the signal control's planted reversal, at the control's own corrected alpha
    Row("controls:signal", "day_boxed", "the signal control's planted reversal", "beats_always_long", "power", POWER_SEEDS,
        planned=0.80, alpha=0.05 / 9),
    # the floor (ADR-0050): an EV exactly at the floor must clear the bound at most at alpha; one at the alternative,
    # at the count the plan asks for, at least at the planned power
    Row("synthetic:at-floor", "synthetic", "the law, its true EV exactly at the floor", "clears_floor", "size", SIZE_SEEDS),
    Row("synthetic:at-alternative", "synthetic", "the law, its true EV at the alternative, at the count the plan requires",
        "clears_floor", "power", POWER_SEEDS, planned=0.80, alpha=0.01),
    # S3 and S10 over seeds: a coin flip is never accepted, and a planted effect at the alternative is, at planned power
    Row("controls-synthetic:null", "synthetic", "the null control, all five checks", "all_five", "size", SIZE_SEEDS),
    Row("controls:null", "day_boxed", "the null control, all five checks", "all_five", "size", SIZE_SEEDS),
    Row("controls-synthetic:signal", "synthetic", "the signal control, all five checks", "all_five", "power", POWER_SEEDS,
        planned=0.80, alpha=0.05 / 9),
    Row("controls:signal", "day_boxed", "the signal control, all five checks", "all_five", "power", POWER_SEEDS,
        planned=0.80, alpha=0.05 / 9),
)


def row(world_key: str, guard: str) -> Row:
    return next(r for r in ROWS if r.key == world_key and r.guard == guard)


WORKERS = "OCCAMS_CALIBRATION_WORKERS"  # how many processes draw at once; fewer on a machine short of memory


def _workers() -> int:
    return max(1, int(os.environ.get(WORKERS) or min(8, (os.cpu_count() or 2))))


_CACHE: dict[tuple[str, int], tuple[tuple[float, ...], ...]] = {}
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


def collect(world: str, seeds: int) -> tuple[tuple[float, ...], ...]:
    """Every seed's p-values for one world, one per guard, computed once per process and shared by
    the rows that read the same world."""
    key = (world, seeds)
    if key not in _CACHE:
        saved = _saved().get(f"{world}|{seeds}")
        if saved is not None and all(len(ps) == len(GUARDS) for ps in saved):
            _CACHE[key] = tuple(tuple(float(x) for x in ps) for ps in saved)
        else:
            tasks = [(world, s) for s in range(1, seeds + 1)]
            with ProcessPoolExecutor(max_workers=_workers()) as pool:
                _CACHE[key] = tuple(pool.map(p_values, tasks, chunksize=4))
            if _SAVE_TO:
                save(_SAVE_TO)              # world by world: a run that is stopped resumes from what it had drawn
    return _CACHE[key]


_SAVE_TO = ""


def save(path: str) -> None:
    """Write every world drawn so far, with what an earlier run of the same code had saved there."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    worlds = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            blob = json.load(f)
        if blob.get("code") == _code_stamp():
            worlds = {k: v for k, v in blob.get("worlds", {}).items() if all(len(p) == len(GUARDS) for p in v)}
    worlds.update({f"{w}|{n}": [list(p) for p in ps] for (w, n), ps in _CACHE.items()})
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"code": _code_stamp(), "worlds": worlds}, f)


def rate(row: Row, alpha: float) -> float:
    """How often the guard lets the world through at ``alpha``: for a size row, the false-positive rate."""
    col = GUARDS.index(row.guard)
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
        for alpha in row.alphas:
            ok, got, bound = within(row, alpha)
            out.append({"engine": row.engine, "guard": row.guard, "world": row.world, "kind": row.kind, "alpha": alpha,
                        "measured": got, "bound": bound, "within": ok, "seeds": row.seeds, "fixed_by": row.fixed_by})
    return out


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    global _SAVE_TO
    strict = "--strict" in argv
    if "--save" in argv:                    # drawn worlds are written as they finish, and read back if this code drew them before
        _SAVE_TO = argv[argv.index("--save") + 1]
        os.environ.setdefault(SAVED, _SAVE_TO)
    rows = table()
    print("The size-and-power table (ADR-0047 §6): each Monte Carlo guard in isolation, on a world whose truth is known.")
    print(f"{'engine':15s} {'guard':18s} {'alpha':>5s} {'measured':>8s} {'bound':>6s}  {'':6s} world")
    out_of = 0
    for r in rows:
        mark = "ok" if r["within"] else "OVER" if r["kind"] == "size" else "UNDER"
        known = r["fixed_by"]
        note = "" if r["within"] or not known else f"  ({known})" if known == RESIDUAL else f"  (a known defect: {known} fixes it)"
        out_of += 0 if r["within"] else 1
        print(f"{r['engine']:15s} {r['guard']:18s} {r['alpha']:5.3f} {r['measured']:8.3f} {r['bound']:6.3f}  {mark:6s} "
              f"{r['world']} [{r['seeds']} seeds]{note}")
    print(f"{len(rows) - out_of} of {len(rows)} rows within tolerance.")
    if _SAVE_TO:
        save(_SAVE_TO)
    return 1 if (strict and out_of) else 0


if __name__ == "__main__":
    raise SystemExit(main())
