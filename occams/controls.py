"""``make null`` and ``make signal`` — the apparatus proves it can refuse and
that it can accept (ADR-0014, ADR-0029). Standing checks S3 and S10.

Both drive the SAME pipeline: a control Hypothesis is registered at alpha 0,
a Strategy is specified, compiled and measured by the synthetic engine, and
the four MEASURED -> FORWARD refusals decide. The null names which refusals
fired; the signal names that all five checks passed. Exit code 0 means the
control did what a control must; 1 means stop and fix the guards.
"""

from __future__ import annotations

import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from occams.config import InformationAxis
from occams.engine import synthetic
from occams.guards import Refused, forward
from occams.hypothesis import (Confirmation, Gates, Hypothesis, PowerPlan, Tier, measure, register)
from occams.measurement import Floor
from occams.register import Register
from occams.strategy import Strategy, StrategyState, transition

ROOT = Path(__file__).resolve().parent.parent
CONTROLS = ROOT / "controls.toml"


@dataclass(frozen=True)
class Outcome:
    kind: str
    accepted: bool
    refusals: tuple[str, ...]
    passes: tuple[str, ...]
    winner_ev: float
    n: int
    required_n: int
    hypothesis_id: str
    spec_hash: str
    register_path: str


def load_controls(path: Path = CONTROLS) -> dict:
    with path.open("rb") as f:
        return tomllib.load(f)


def _effect(kind: str, cfg: dict):
    if kind == "null":
        return synthetic.flat(0.0)
    if kind == "signal":
        return synthetic.flat(float(cfg["signal"]["planted_ev_net_r"]))
    raise ValueError(kind)


def _reverting_walk(name: str, *, days: int, seed: int, sigma_daily: float, planted: float, runs: int,
                    start: float = 100.0, range_fraction: float = 0.5):
    """The signal control's world under ADR-0043: a driftless walk whose
    return on the day after ``runs`` lower closes — and on no other day —
    carries the planted size. An entry can find that; always-long rides it
    one day in 2**runs; a drift on every day is what the fifth check
    refuses. Bars shaped as ``random_walk`` shapes them."""
    import zlib

    from occams.data.bars import Bars

    rng = np.random.default_rng([seed, zlib.crc32(name.encode("utf-8"))])
    z = rng.standard_normal(days)
    closes = np.empty(days)
    prev = start
    for t in range(days):
        down_run = t > runs and all(closes[t - k] < closes[t - k - 1] for k in range(1, runs + 1))
        prev = prev * float(np.exp((planted if down_run else 0.0) + sigma_daily * z[t]))
        closes[t] = prev
    opens = np.concatenate(([start], closes[:-1]))
    span = np.abs(closes - opens) * range_fraction + start * sigma_daily * 0.25 * rng.random(days)
    highs = np.maximum(opens, closes) + span
    lows = np.minimum(opens, closes) - span
    vol = np.full(days, 1e6)
    return Bars(name, tuple(map(float, opens)), tuple(map(float, highs)), tuple(map(float, lows)),
                tuple(map(float, closes)), tuple(map(float, vol)), tuple(range(days)))


def _day_boxed_measurement(kind: str, cfg: dict, seed: int, spec_hash_of, floor, gates):
    """The same control through the real engine: a driftless random walk
    entered by a coin flip for the null; for the signal, a walk whose day
    after ``planted_runs`` lower closes carries the planted return, entered
    by a down-run of that length (ADR-0043)."""
    from occams.data.bars import random_walk
    from occams.engine import day_boxed
    from occams.spec import (Capability, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType, Side, Sizing,
                             Stop, StopKind, StrategySpec, UniverseRule)

    d = cfg["day_boxed"]
    if kind == "signal":
        runs = int(d["planted_runs"])
        world = {n: _reverting_walk(n, days=int(d["days"]), seed=seed, sigma_daily=float(d["sigma_daily"]),
                                    planted=float(d["planted_return_daily"]), runs=runs) for n in d["groups"]}
        entry = Entry(EntryKind.DOWN_RUN, Side.LONG, (("runs", runs),))
    else:
        world = {n: random_walk(n, days=int(d["days"]), seed=seed, sigma_daily=float(d["sigma_daily"]), drift_daily=0.0)
                 for n in d["groups"]}
        entry = Entry(EntryKind.COIN_FLIP, Side.LONG, (("seed", seed),))
    template = StrategySpec(entries=(entry,), exits=(Exit(ExitKind.TIME, (("bars", 1),)),),
                            stop=Stop(StopKind.PERCENT, float(d["stop_percent"][0])), sizing=Sizing(),
                            order_type=OrderType.MARKET, horizon=Horizon.INTRADAY,
                            universe=UniverseRule((("world", "synthetic-random-walk"),)),
                            required_capabilities=frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS}),
                            axis=InformationAxis.PRICE_DAILY)
    axes = {"stop": [float(x) for x in d["stop_percent"]], "target": [float(x) for x in d["target_multiple"]]}

    def cell(t, p):
        return t.replace(stop=Stop(StopKind.PERCENT, p["stop"]),
                         exits=(Exit(ExitKind.TIME, (("bars", 1),)), Exit(ExitKind.TARGET_R, (("multiple", p["target"]),))))

    m = day_boxed.measure(template, axes, cell, world, seed=seed, cost_in_r=float(d["cost_in_r"]),
                          null_draws=int(cfg["gates"]["null_draws"]))
    return template, m


def run(kind: str, cfg: dict, register_dir: Path, *, seed: int | None = None, engine: str = "synthetic") -> Outcome:
    if engine == "day_boxed":
        return run_day_boxed(kind, cfg, register_dir, seed=seed)
    reg = Register(register_dir / "register.jsonl")
    axes = {k: [float(x) for x in v] for k, v in cfg["sweep"].items()}
    cells = 1
    for v in axes.values():
        cells *= len(v)
    w = cfg["world"]
    seed = int(w["seed"] if seed is None else seed)
    groups = list(w["groups"])
    available = int(round(w["years"] * w["trades_per_group_year"])) * len(groups)

    h = Hypothesis(
        id=f"CONTROL-{kind.upper()}", tier=Tier.MECHANISM, axis=InformationAxis.PRICE_DAILY,
        mechanism="apparatus test: " + ("random entry has no edge" if kind == "null" else "a planted effect at the floor is detectable"),
        if_true="the pipeline refuses it" if kind == "null" else "the pipeline accepts it",
        if_false="the guards are decorative" if kind == "null" else "the gates are jointly unsatisfiable",
        falsifier="the opposite decision",
        floor=Floor(float(cfg["floor"]["ev_net_r"]), float(cfg["floor"]["min_trades_per_year"])),
        power_plan=PowerPlan(float(cfg["power"]["sigma_r"]), float(cfg["power"]["alpha"]),
                             float(cfg["power"]["power"]), available),
        gates=Gates(int(cfg["gates"]["plateau_cells"]), float(cfg["gates"]["plateau_slack"]),
                    float(cfg["gates"]["loo_min_fraction"])),
        search_space_size=cells, capability=True)
    h = register(h, confirmation=Confirmation(by="apparatus", human=False), parent=None, register=reg)

    s = Strategy.specify({"kind": "coin_flip" if kind == "null" else "planted",
                          "stop": float(axes["stop"][0]), "hold": float(axes["hold"][0]),
                          "engine": synthetic.NAME}, hypothesis_id=h.id)
    s = transition(s, StrategyState.COMPILED, register=reg)
    m = synthetic.measure(spec_hash=s.spec_hash, seed=seed, axes=axes, groups=groups,
                          years=float(w["years"]), trades_per_group_year=float(w["trades_per_group_year"]),
                          sigma_r=float(cfg["power"]["sigma_r"]), cost_in_r=float(w["cost_in_r"]),
                          effect=_effect(kind, cfg), null_draws=int(cfg["gates"]["null_draws"]))
    h = measure(h, m, register=reg)
    s = transition(s, StrategyState.MEASURED, register=reg, measurement=m)
    try:
        s = transition(s, StrategyState.FORWARD, register=reg, hypothesis=h)
        accepted, refusals = True, ()
    except Refused as e:
        accepted, refusals = False, tuple(r.reason for r in e.refusals)
    return Outcome(kind, accepted, refusals, forward.passes(m, h), m.winner.ev, m.winner.n,
                   h.required_n, h.id, s.spec_hash, str(reg.path))


def run_day_boxed(kind: str, cfg: dict, register_dir: Path, *, seed: int | None = None) -> Outcome:
    from occams.strategy import Strategy as _Strategy

    reg = Register(register_dir / "register.jsonl")
    d = cfg["day_boxed"]
    seed = int(d["seed"] if seed is None else seed)
    cells = len(d["stop_percent"]) * len(d["target_multiple"])
    available = int(d["days"]) * len(d["groups"])
    floor = Floor(float(cfg["floor"]["ev_net_r"]), float(cfg["floor"]["min_trades_per_year"]))
    gates = Gates(int(cfg["gates"]["plateau_cells"]), float(cfg["gates"]["plateau_slack"]),
                  float(cfg["gates"]["loo_min_fraction"]))
    h = Hypothesis(
        id=f"CONTROL-{kind.upper()}-DAY-BOXED", tier=Tier.MECHANISM, axis=InformationAxis.PRICE_DAILY,
        mechanism="apparatus test through the day-boxed engine: " + (
            "random entry has no edge" if kind == "null" else "a planted reversal at the floor is detectable over always-long"),
        if_true="the pipeline refuses it" if kind == "null" else "the pipeline accepts it",
        if_false="the guards are decorative" if kind == "null" else "the gates are jointly unsatisfiable",
        falsifier="the opposite decision", floor=floor,
        power_plan=PowerPlan(float(d["sigma_r"]), float(cfg["power"]["alpha"]), float(cfg["power"]["power"]), available),
        gates=gates, search_space_size=cells, capability=True)
    h = register(h, confirmation=Confirmation(by="apparatus", human=False), parent=None, register=reg)
    template, m = _day_boxed_measurement(kind, cfg, seed, None, floor, gates)
    s = _Strategy.from_spec(template, hypothesis_id=h.id)
    s = transition(s, StrategyState.COMPILED, register=reg)
    h = measure(h, m, register=reg)
    s = transition(s, StrategyState.MEASURED, register=reg, measurement=m)
    try:
        s = transition(s, StrategyState.FORWARD, register=reg, hypothesis=h)
        accepted, refusals = True, ()
    except Refused as e:
        accepted, refusals = False, tuple(r.reason for r in e.refusals)
    return Outcome(kind + "/day_boxed", accepted, refusals, forward.passes(m, h), m.winner.ev, m.winner.n,
                   h.required_n, h.id, s.spec_hash, str(reg.path))


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    engine = "day_boxed" if "--engine=day_boxed" in argv else "synthetic"
    argv = [a for a in argv if not a.startswith("--engine")]
    if not argv or argv[0] not in ("null", "signal"):
        print("usage: python -m occams.controls null|signal [register_dir] [--engine=day_boxed]")
        return 2
    kind = argv[0]
    reg_dir = Path(argv[1]) if len(argv) > 1 else Path(tempfile.mkdtemp(prefix="occams-controls-"))
    o = run(kind, load_controls(), reg_dir, engine=engine)
    print(f"{kind.upper()} CONTROL [{engine}] — {o.hypothesis_id}, spec {o.spec_hash[:12]}, "
          f"N = {o.n} (required {o.required_n}), winner EV = {o.winner_ev:+.4f} net R")
    from occams import identity

    # an apparatus control checks a change *before* it is committed, so it runs on the tree as it is and says what that was
    print(f"apparatus control, exempt from the clean-code rule (ADR-0055): {identity.describe()}")
    if kind == "null":
        if o.accepted:
            print("ACCEPTED at MEASURED -> FORWARD. A coin flip passed. STOP AND FIX THE GUARDS (S3).")
            return 1
        print("REFUSED at MEASURED -> FORWARD, by:")
        for r in o.refusals:
            print(f"  - {r}")
        print(f"checks that passed: {list(o.passes) or 'none'}  (register: {o.register_path})")
        return 0
    if o.accepted:
        print(f"ACCEPTED at MEASURED -> FORWARD: all five checks passed — {list(o.passes)}  (register: {o.register_path})")
        return 0
    print("REFUSED at MEASURED -> FORWARD. The planted effect was not accepted — the gates have become unsatisfiable (S10). Refused by:")
    for r in o.refusals:
        print(f"  - {r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
