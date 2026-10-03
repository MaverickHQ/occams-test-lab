"""The regime classifier, frozen first (F11, D13, ADR-0005, M7.6), and the
regime proposer built on it.

The classifier's parameters are chosen on a priori grounds from a small
declared grid, calibrated **only on the definition period** — the bars it
is given are checked against the definition bounds and anything outside
them is refused — and then frozen with a hash. Its label at ``t`` is a
function of bars strictly before ``t``; ``assert_causal`` perturbs the
future and refuses a labeller whose past changes.
"""

from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass
from itertools import product
from collections.abc import Callable

import numpy as np

from occams.config import InformationAxis
from occams.data.bars import Bars
from occams.hypothesis import Gates
from occams.measurement import Floor
from occams.proposers.base import Draft, Proposer, Sandbox, Sweep


from occams.spec.spec import Regime  # noqa: E402 — the closed label set lives with the spec (identity)


class ClusterLevel(enum.Enum):
    INDEX = "index"            # one label per day for the whole set
    INSTRUMENT = "instrument"  # one label per day per name


class NonCausal(ValueError):
    pass


class OutsideDefinitionPeriod(ValueError):
    pass


# The a priori grid (ADR-0005): small, declared here, never tuned to a strategy.
GRID = {"short": (10, 20), "long": (50, 100, 200), "band": (0.0, 0.01)}
MIN_SHARE = 0.10  # every regime must occupy at least this share of labelled days


@dataclass(frozen=True)
class RegimeClassifier:
    short: int
    long: int
    band: float
    level: ClusterLevel

    def __post_init__(self):
        if not (0 < self.short < self.long):
            raise ValueError("short lookback must be positive and shorter than long")
        if not isinstance(self.level, ClusterLevel):
            raise TypeError("level is a closed enum")

    @property
    def frozen_hash(self) -> str:
        return hashlib.sha256(json.dumps({"short": self.short, "long": self.long, "band": self.band,
                                          "level": self.level.value}, sort_keys=True).encode()).hexdigest()

    def label_at(self, bars: Bars, t: int) -> Regime | None:
        """The label for bar ``t``, from closes [t-long, t) — nothing at or after ``t``."""
        if t < self.long:
            return None
        closes = bars.close[t - self.long:t]
        ma_s = sum(closes[-self.short:]) / self.short
        ma_l = sum(closes) / self.long
        if ma_s > ma_l * (1 + self.band):
            return Regime.UP
        if ma_s < ma_l * (1 - self.band):
            return Regime.DOWN
        return Regime.RANGING

    def labels(self, bars: Bars) -> tuple[Regime | None, ...]:
        return tuple(self.label_at(bars, t) for t in range(bars.n))


def _score(clf: RegimeClassifier, bars_by_name: dict[str, Bars]) -> float | None:
    """A priori criterion: persistent labels with every regime present."""
    persist, total = 0, 0
    counts = {r: 0 for r in Regime}
    for b in bars_by_name.values():
        labs = [x for x in clf.labels(b) if x is not None]
        for a, c in zip(labs, labs[1:], strict=False):
            persist += a is c
            total += 1
        for x in labs:
            counts[x] += 1
    n = sum(counts.values())
    if n == 0 or total == 0 or min(counts.values()) / n < MIN_SHARE:
        return None
    return persist / total


def calibrate(bars_by_name: dict[str, Bars], *, definition_bounds: tuple[int, int], level: ClusterLevel,
              seed: int) -> RegimeClassifier:
    """Choose from GRID on the definition period only. Deterministic; the
    seed breaks exact ties and nothing else."""
    lo, hi = definition_bounds
    for name, b in bars_by_name.items():
        if any(not (lo <= d < hi) for d in b.day):
            raise OutsideDefinitionPeriod(f"{name} carries bars outside the definition period [{lo}, {hi}); "
                                          f"the classifier is calibrated on the definition period and nothing else (D13)")
    candidates = []
    for s, l, band in product(GRID["short"], GRID["long"], GRID["band"]):  # noqa: E741
        clf = RegimeClassifier(s, l, band, level)
        sc = _score(clf, bars_by_name)
        if sc is not None:
            candidates.append((sc, clf))
    if not candidates:
        raise ValueError("no grid point labels every regime on the definition period; the period is too short")
    best = max(c[0] for c in candidates)
    ties = [clf for sc, clf in candidates if abs(sc - best) < 1e-12]
    rng = np.random.default_rng(seed)
    return ties[int(rng.integers(0, len(ties)))]


def assert_causal(label_at: Callable[[Bars, int], object], bars: Bars, *, seed: int, trials: int = 20) -> None:
    """Perturb everything at or after ``t``; the label at ``t`` may not move."""
    rng = np.random.default_rng(seed)
    n = bars.n
    for _ in range(trials):
        t = int(rng.integers(1, n))
        before = label_at(bars, t)
        scale = float(1.0 + rng.choice([-0.3, 0.3]))
        f = lambda seq, t=t, scale=scale: tuple(v * scale if i >= t else v for i, v in enumerate(seq))  # noqa: E731
        perturbed = Bars(bars.name, f(bars.open), f(bars.high), f(bars.low), f(bars.close), bars.volume, bars.day,
                         close_at=bars.close_at)
        after = label_at(perturbed, t)
        if before != after:
            raise NonCausal(f"label at t={t} changed from {before} to {after} when bars at or after t changed")


class RegimeProposer(Proposer):
    """Drafts a regime-conditional mechanism question per regime, on a
    frozen classifier. Every number it emits is its own declaration or a
    computation over bars; retrieved text becomes references and quotes."""

    name = "regime"

    def __init__(self, classifier: RegimeClassifier, *, floor: Floor, sigma_r: float, sigma_provenance: str,
                 power: float, gates: Gates, sweep: Sweep):
        self.classifier = classifier
        self.floor, self.sigma_r, self.sigma_provenance = floor, sigma_r, sigma_provenance
        self.power, self.gates, self.sweep = power, gates, sweep

    def propose(self, sandbox: Sandbox, regime: Regime, *, sources: tuple[str, ...] = ()) -> tuple[Draft, ...]:
        refs, surfaced = [], []
        for url in sources:
            q = sandbox.retrieve(url)
            refs.append(q.reference)
            surfaced.extend(f"{q.reference}: {line}" for line in q.flagged)
        d = Draft(
            proposer=self.name, axis=InformationAxis.REGIME,
            mechanism=(f"In the {regime.value} regime as labelled by classifier {self.classifier.frozen_hash[:12]} "
                       f"({self.classifier.level.value}-level), breakout entries carry positive EV in net R "
                       f"because participants under-react to continuation within the regime"),
            if_true="the winner cell clears the declared floor and beats random entry at the corrected alpha",
            if_false="within-regime continuation is not distinguishable from random entry after costs",
            falsifier="the winner cell's EV in net R at or below the null's corrected quantile, or below the floor",
            floor=self.floor, sweep=self.sweep, sigma_r=self.sigma_r, sigma_provenance=self.sigma_provenance,
            power=self.power, gates=self.gates,
            sources=tuple(refs), surfaced=tuple(surfaced),
            notes=f"classifier frozen at {self.classifier.frozen_hash}; regime={regime.value}")
        return (d,)


# ---- freezing: the classifier's own registration (ADR-0005) --------------------

class AlreadyFrozen(RuntimeError):
    pass


def frozen(register) -> RegimeClassifier | None:
    """The classifier the Register holds, if one was frozen."""
    rows = [r for r in register.records() if r["type"] == "ClassifierFrozen"]
    if not rows:
        return None
    r = rows[-1]
    return RegimeClassifier(r["short"], r["long"], r["band"], ClusterLevel(r["level"]))


def shares(clf: RegimeClassifier, bars_by_name: dict[str, Bars]) -> dict[str, float]:
    counts = {r.value: 0 for r in Regime}
    for b in bars_by_name.values():
        for x in clf.labels(b):
            if x is not None:
                counts[x.value] += 1
    n = sum(counts.values()) or 1
    return {k: v / n for k, v in counts.items()}


def freeze(archive, cfg, *, register, level: ClusterLevel, index_name: str, seed: int, config_sha: str,
           supersedes: str | None = None, reason: str = "", universe: str = "", names: tuple[str, ...] = ()
           ) -> RegimeClassifier:
    """Calibrate on the archive's definition partition — one calendar across
    every series — and commit the result to the Register. Once: a second
    freeze is refused unless it names the frozen hash it supersedes and
    says why (ADR-0005: a different classifier is a recorded supersession,
    not a re-run). ``universe`` names the frozen calendar the definition
    window is cut from (programme 2 has one per universe, ADR-0038);
    ``names`` restricts the series calibrated on — at index level the
    index must be among them."""
    from occams.data.partitions import Partitions

    current = frozen(register)
    if current is not None and (supersedes != current.frozen_hash or not reason.strip()):
        raise AlreadyFrozen("a classifier is already frozen in this Register; freezing again is a recorded supersession — "
                            "name the frozen hash it supersedes and the reason (ADR-0005)")
    parts = Partitions.from_config(cfg)
    latest = archive.latest_bars()
    if not latest:
        raise ValueError("the archive holds no bars")
    if level is ClusterLevel.INDEX and index_name not in latest:
        raise ValueError(f"index-level labelling names {index_name!r}, which is not in the archive")
    from occams.data.partitions import declared_universe, span_for
    if names:
        missing = [n for n in names if n not in latest]
        if missing:
            raise ValueError(f"names not in the archive: {missing}")
        if level is ClusterLevel.INDEX and index_name not in names:
            raise ValueError(f"index-level labelling reads {index_name!r}, which is not among the names calibrated on")
        latest = {n: latest[n] for n in names}
    if universe:
        u = declared_universe(register, universe)
        if u is None:
            raise ValueError(f"universe {universe!r} is not declared in this Register (M12.1)")
        members = {n: b for n, (b, _a) in archive.latest_bars().items() if n in u["members"]}
        span = span_for(register, members, parts, universe=universe)   # the universe's frozen calendar (ADR-0038)
    else:
        span = span_for(register, {n: b for n, (b, _a) in latest.items()}, parts)   # the frozen calendar (ADR-0038)
    bounds = parts.bounds_over(*span)["definition"]
    world = {}
    for name, (bars, _acts) in latest.items():
        sliced, _b = parts.slice(bars, "definition", span=span)
        if sliced.n:
            world[name] = sliced  # a name listed after the definition period contributes nothing to it
    if not world:
        raise ValueError("no series has bars in the definition period")
    clf = calibrate(world, definition_bounds=bounds, level=level, seed=seed)
    sc = _score(clf, world)
    first_at = min(b.close_at[0] for b in world.values() if b.close_at) if any(b.close_at for b in world.values()) else ""
    last_at = max(b.close_at[-1] for b in world.values() if b.close_at) if any(b.close_at for b in world.values()) else ""
    register.append(register.ClassifierFrozen(clf.frozen_hash, clf.short, clf.long, clf.band, level.value, index_name,
                                              bounds[0], bounds[1], first_at, last_at, tuple(sorted(world)),
                                              float(sc or 0.0), shares(clf, world), int(seed), config_sha,
                                              supersedes or "", reason))
    return clf


def main(argv=None) -> int:
    import argparse
    from pathlib import Path

    from occams.config import load
    from occams.data.archive import BarArchive
    from occams.register import Register
    from occams.whatif import config_sha

    ap = argparse.ArgumentParser(prog="python -m occams classifier")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("freeze")
    f.add_argument("--archive", required=True, type=Path)
    f.add_argument("--register", required=True, type=Path)
    f.add_argument("--level", choices=[c.value for c in ClusterLevel], default=ClusterLevel.INDEX.value)
    f.add_argument("--index", default="SPY")
    f.add_argument("--seed", type=int, required=True)
    f.add_argument("--config", default=None, help="the programme's config; default: the working directory's occams.toml")
    f.add_argument("--supersedes", default=None, help="the frozen hash this replaces")
    f.add_argument("--reason", default="")
    f.add_argument("--universe", default="", help="the declared universe whose frozen calendar cuts the definition window (M12)")
    f.add_argument("--names", default="", help="comma list: calibrate on these series only (the index among them at index level)")
    sh = sub.add_parser("show")
    sh.add_argument("--register", required=True, type=Path)
    a = ap.parse_args(argv)
    reg = Register(a.register)
    if a.cmd == "show":
        rows = [r for r in reg.records() if r["type"] == "ClassifierFrozen"]
        if not rows:
            print("no classifier is frozen")
            return 1
        r = rows[-1]
        print(f"frozen {r['frozen_hash'][:12]}: short {r['short']} / long {r['long']} / band {r['band']}, {r['level']}-level on {r['index_name']}; "
              f"definition days [{r['definition_start_day']}, {r['definition_end_day']}) = {r['definition_first_at'][:10]} -> {r['definition_last_at'][:10]}; "
              f"persistence {r['persistence']:.3f}; shares {r['shares']}; names {list(r['names'])}")
        return 0
    cfg = load(a.config)
    try:
        clf = freeze(BarArchive(a.archive), cfg, register=reg, level=ClusterLevel(a.level), index_name=a.index,
                     universe=a.universe, names=tuple(n.strip().upper() for n in a.names.split(",") if n.strip()),
                     seed=a.seed, config_sha=config_sha(cfg), supersedes=a.supersedes, reason=a.reason)
    except (AlreadyFrozen, ValueError, OutsideDefinitionPeriod) as e:
        print(f"REFUSED: {e}")
        return 1
    r = [x for x in reg.records() if x["type"] == "ClassifierFrozen"][-1]
    print(f"frozen {clf.frozen_hash[:12]}: short {clf.short} / long {clf.long} / band {clf.band}, {a.level}-level on {a.index}")
    print(f"definition partition days [{r['definition_start_day']}, {r['definition_end_day']}) = "
          f"{r['definition_first_at'][:10]} -> {r['definition_last_at'][:10]} over {list(r['names'])}")
    print(f"persistence {r['persistence']:.3f}; label shares " + ", ".join(f"{k} {v:.1%}" for k, v in r["shares"].items()))
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())


# ---- DRAFT-003's template and the pre-committed numbers it needs ------------------

def template_for(clf: RegimeClassifier, *, label: Regime, index_name: str, lookback: int = 20,
                 stop_percent: float = 2.0, target_multiple: float = 2.0, hold_bars: int = 1):
    """The regime-gated breakout of DRAFT-003, as a spec. The sweep edits
    stop and target; everything else is fixed here and is identity."""
    from occams.config import InformationAxis
    from occams.spec.spec import (Capability, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType, RegimeGate, Side,
                                  Sizing, Stop, StopKind, StrategySpec, UniverseRule)

    return StrategySpec(
        entries=(Entry(EntryKind.BREAKOUT_HIGH, Side.LONG, (("lookback", lookback),)),),
        exits=(Exit(ExitKind.TIME, (("bars", hold_bars),)), Exit(ExitKind.TARGET_R, (("multiple", target_multiple),))),
        stop=Stop(StopKind.PERCENT, stop_percent), sizing=Sizing(), order_type=OrderType.STOP,
        horizon=Horizon.INTRADAY, universe=UniverseRule((("venue", "NYSE"), ("class", "us_large"))),
        required_capabilities=frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS}),
        axis=InformationAxis.REGIME, regime=RegimeGate(clf.frozen_hash, label, index_name))


def precommit(template, *, archive, cfg, register, seed: int, sweep=None) -> dict:
    """Everything the power plan needs, from the DEFINITION partition only
    (D13): the signal rate per name-year, the trades the measurement
    partition therefore affords, and the measured intra-cluster correlation
    (M7.7). Nothing here touches the measurement partition. With ``sweep``,
    the trades promised are the sweep's thinnest cell's, not the template's
    signals (M13.9, as the survey path since 2026-09-20): the guard at
    measurement counts the winning cell's own trades, and a long hold boxes
    most signals out."""
    from occams.data.partitions import Partitions
    from occams.engine import day_boxed, position_boxed
    from occams.engine.regime_gate import RegimeContext
    from occams.proposers.clustering import measure_clustering
    from occams.spec.compile import to_engine
    from occams.spec.spec import Horizon

    parts = Partitions.from_config(cfg)
    latest = {n: b for n, (b, _a) in archive.latest_bars().items()}
    from occams.data.partitions import span_for
    span = span_for(register, latest, parts)   # the frozen calendar (ADR-0038)
    b = parts.bounds_over(*span)
    definition = {n: parts.slice(bb, "definition", span=span)[0] for n, bb in latest.items()}
    definition = {n: bb for n, bb in definition.items() if bb.n}
    ctx = RegimeContext.from_register(register, archive) if template.regime is not None else None
    engine = position_boxed if template.horizon is Horizon.MULTI_DAY else day_boxed   # D6: the horizon selects
    trades = engine.run(to_engine(template), definition, seed=seed, regime=ctx)
    # ADR-0043: always-long at the template's geometry and gate, so the fifth gate is shown passable before alpha moves
    from occams.spec.compile import derived_capabilities
    from occams.spec.spec import Entry, EntryKind, OrderType, Side

    base_spec = template.replace(entries=(Entry(EntryKind.ALWAYS, Side.LONG, ()),), order_type=OrderType.MARKET)
    base_spec = base_spec.replace(required_capabilities=derived_capabilities(base_spec))
    base = engine.run(to_engine(base_spec), definition, seed=seed, regime=ctx)
    def_days = b["definition"][1] - b["definition"][0]
    meas_days = b["measurement"][1] - b["measurement"][0]
    names_in_measurement = [n for n, bb in latest.items() if parts.slice(bb, "measurement", span=span)[0].n]
    rate_per_name_day = len(trades) / max(1, sum(bb.n for bb in definition.values()))
    available = int(rate_per_name_day * meas_days * len(names_in_measurement) * (252 / 365.25))
    template_available, thinnest = available, None
    if sweep is not None and sweep.size:
        import itertools

        from occams.question import apply_cell

        counts = []
        for values in itertools.product(*(v for _k, v in sweep.axes)):
            point = dict(zip((k for k, _v in sweep.axes), values, strict=True))
            n_cell = len(engine.run(to_engine(apply_cell(template, point)), definition, seed=seed, regime=ctx))
            counts.append((n_cell, point))
        n_thin, point_thin = min(counts, key=lambda c: c[0])
        thin_available = int(n_thin / max(1, sum(bb.n for bb in definition.values())) * meas_days * len(names_in_measurement) * (252 / 365.25))
        thinnest = {"point": point_thin, "definition_trades": int(n_thin), "available_n": thin_available}
        available = min(available, thin_available)
    # the declared level: a classifier's own when gated; else same-day clusters across a pooled set (INDEX), one name alone (INSTRUMENT)
    level = ctx.classifier.level if ctx else (ClusterLevel.INDEX if len(definition) > 1 else ClusterLevel.INSTRUMENT)
    measurable = len({t.day for t in trades}) >= 2 and len(trades) >= 3
    cm = measure_clustering([t.as_trade() for t in trades], level=level,
                            provenance=f"definition partition {b['definition']}, {len(trades)} signals on {sorted(definition)}") if measurable else None
    return {"definition_trades": len(trades), "definition_days": def_days, "measurement_days": meas_days,
            "definition_ev_net": (sum(t.net_r for t in trades) / len(trades)) if trades else None,
            "baseline_trades": len(base), "baseline_ev_net": (sum(t.net_r for t in base) / len(base)) if base else None,
            "names": names_in_measurement, "rate_per_name_day": rate_per_name_day, "available_n": available,
            "template_available_n": template_available, "thinnest_cell": thinnest,
            "clustering": cm, "context": ctx, "definition_bars": definition, "measurement_bounds": b["measurement"]}


def definition_surface(template, sweep, definition_bars, *, ctx, seed: int) -> list[dict]:
    """ADR-0045, shown before alpha moves: every cell of the sweep on the
    definition partition with its EV, always-long at its own geometry and
    gate, and the margin — sorted by margin, the surface's winner first.
    Definition data only (D13)."""
    from itertools import product

    from occams.engine import day_boxed, position_boxed
    from occams.engine.day_boxed import baseline_summary
    from occams.question import apply_cell
    from occams.spec.compile import to_engine
    from occams.spec.spec import Horizon

    engine = position_boxed if template.horizon is Horizon.MULTI_DAY else day_boxed
    axes = sweep.as_dict()
    out = []
    for values in product(*axes.values()):
        params = dict(zip(axes, values, strict=True))
        c = to_engine(apply_cell(template, params))
        trades = engine.run(c, definition_bars, seed=seed, regime=ctx, audit_fills=False)
        base_ev, _by = baseline_summary(engine.always_long_trades(c, definition_bars, seed=seed, cost_in_r=0.0, regime=ctx))
        if not trades or base_ev is None:
            continue
        ev = sum(t.net_r for t in trades) / len(trades)
        out.append({"params": params, "n": len(trades), "ev": ev, "baseline_ev": base_ev, "margin": ev - base_ev})
    return sorted(out, key=lambda r: -r["margin"])


def axis_sensitivity(template, sweep, definition_bars, *, ctx, seed: int) -> dict[str, float]:
    """For each sweep axis, the largest fraction of definition-partition trades
    whose outcome changes between two cells that differ only on that axis.
    0.0 is an inert axis: every cell along it produces the same trades, and
    the search-space size it adds is bought for nothing. Definition data
    only — never the measurement partition (D13). Reported, not thresholded:
    what counts as too little is the author's call."""
    from itertools import product

    from occams.engine import day_boxed, position_boxed
    from occams.question import apply_cell
    from occams.spec.compile import to_engine
    from occams.spec.spec import Horizon

    axes = sweep.as_dict()
    names = list(axes)
    engine = position_boxed if template.horizon is Horizon.MULTI_DAY else day_boxed
    outcomes = {}
    for idx in product(*(range(len(axes[a])) for a in names)):
        params = {a: float(axes[a][i]) for a, i in zip(names, idx, strict=True)}
        trades = engine.run(to_engine(apply_cell(template, params)), definition_bars, seed=seed, regime=ctx, audit_fills=False)
        outcomes[idx] = tuple((round(t.gross_r, 9), t.reason) for t in trades)
    sens = {}
    for ai, axis in enumerate(names):
        if len(axes[axis]) < 2:
            continue
        worst = 0.0
        for idx, out in outcomes.items():
            for j in range(idx[ai] + 1, len(axes[axis])):
                other = outcomes[idx[:ai] + (j,) + idx[ai + 1:]]
                differ = sum(1 for x, y in zip(out, other, strict=False) if x != y) + abs(len(out) - len(other))
                worst = max(worst, differ / max(1, len(out), len(other)))
        sens[axis] = worst
    return sens


def inert_axes(template, sweep, definition_bars, *, ctx, seed: int) -> list[str]:
    """The sweep axes along which no definition-partition trade changes."""
    return [a for a, s in axis_sensitivity(template, sweep, definition_bars, ctx=ctx, seed=seed).items() if s == 0.0]
