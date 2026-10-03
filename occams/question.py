"""A Question: a Hypothesis, the template spec it is measured with, and the
declared sweep — everything the first real question needs (M8.1-M8.5).

Registration goes through the accountant with a human confirmation and
the power check refuses an underpowered question before it runs (M8.2).
Measurement reads the archive's measurement partition through the engine
the horizon selects, and the Verdict is reached against the floor declared
beforehand: supported iff the five refusals all pass on the winner cell,
null otherwise, with the refusals named (M8.3). The Verdict freezes the
winner cell's hash and records the template's as the family (ADR-0036).
The Monte Carlo path distribution behind it is archived by content hash
(M8.5). Then the implementation Hypothesis for the winner registers from
the same axis (M8.4).
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, replace
from typing import ClassVar

import numpy as np

from occams.config import Config, InformationAxis
from occams.costs.equity import EquityCosts, InstrumentClass
from occams.data.actions import ActionSeries
from occams.data.archive import BarArchive
from occams.data.bars import Bars
from occams.data.partitions import Partitions
from occams.guards import Refused, forward
from occams.hypothesis import (Confirmation, Gates, Hypothesis, HypothesisState, PowerPlan, Tier, Verdict, measure,
                               resolve)
from occams.hypothesis import register as _register_hypothesis  # the Register store is passed as ``register=``
from occams.ledger.alpha_budget import AlphaBudget, Consumed
from occams.measurement import Floor, Measurement
from occams.proposers.base import Draft, Sweep, to_hypothesis
from occams.register import PathsArchived, Register, Store, _plain
from occams.spec.spec import Exit, ExitKind, Horizon, Stop, StrategySpec
from occams.strategy import Strategy, StrategyState, transition

# How a sweep axis edits the template. Closed: a new axis kind is a code change.
AXIS_KINDS = ("stop", "target", "hold", "lookback")


def apply_cell(template: StrategySpec, params: dict[str, float]) -> StrategySpec:
    spec = template
    for name, value in params.items():
        if name == "stop":
            spec = spec.replace(stop=Stop(spec.stop.kind, float(value), spec.stop.lookback))
        elif name == "target":
            others = tuple(x for x in spec.exits if x.kind is not ExitKind.TARGET_R)
            spec = spec.replace(exits=others + (Exit(ExitKind.TARGET_R, (("multiple", float(value)),)),))
        elif name == "hold":
            others = tuple(x for x in spec.exits if x.kind is not ExitKind.TIME)
            spec = spec.replace(exits=(Exit(ExitKind.TIME, (("bars", float(value)),)),) + others)
        elif name == "lookback":
            spec = spec.replace(entries=tuple(replace(e, params=tuple((k, float(value)) if k == "lookback" else (k, v)
                                                                       for k, v in e.params)) for e in spec.entries))
        else:
            raise ValueError(f"sweep axis {name!r} is not one of {AXIS_KINDS}")
    return spec


@dataclass(frozen=True)
class Question:
    hypothesis: Hypothesis
    template: StrategySpec
    sweep: Sweep
    instrument_class: InstrumentClass = InstrumentClass.US_LARGE
    instrument_currency: str = "USD"

    @property
    def id(self) -> str:
        return self.hypothesis.id

    def to_json(self) -> str:
        return json.dumps({"hypothesis": _plain(self.hypothesis), "template": self.template.identity(),
                           "sweep": self.sweep.as_dict(), "instrument_class": self.instrument_class.value,
                           "instrument_currency": self.instrument_currency}, sort_keys=True)

    @classmethod
    def from_json(cls, text: str) -> "Question":
        d = json.loads(text)
        h = d["hypothesis"]
        hyp = Hypothesis(id=h["id"], tier=Tier(h["tier"]), axis=InformationAxis(h["axis"]), mechanism=h["mechanism"],
                         if_true=h["if_true"], if_false=h["if_false"], falsifier=h["falsifier"],
                         floor=Floor(**h["floor"]),
                         power_plan=PowerPlan(**{k: v for k, v in h["power_plan"].items()}),
                         gates=Gates(**h["gates"]), search_space_size=h["search_space_size"],
                         parent_id=h.get("parent_id"), supersedes=h.get("supersedes"), capability=h.get("capability", False),
                         distinction=h.get("distinction"), state=HypothesisState(h["state"]),
                         registered_by=h.get("registered_by"), alpha_spent=h.get("alpha_spent"),
                         config_sha=h.get("config_sha"), spec_hash=h.get("spec_hash"), survey=h.get("survey"))
        return cls(hyp, StrategySpec.from_json(json.dumps(d["template"])),
                   Sweep(tuple((k, tuple(v)) for k, v in d["sweep"].items())),
                   InstrumentClass(d["instrument_class"]), d["instrument_currency"])


def _queued(cls):
    cls.__question_record__ = True
    return cls


@_queued
@dataclass(frozen=True)
class QuestionQueued:
    hypothesis_id: str
    question_json: str


class QuestionQueue(Store):
    """Registered questions waiting to run. Append-only; the loop reads it."""

    marker: ClassVar[str] = "__question_record__"
    name: ClassVar[str] = "Question queue"

    def enqueue(self, q: Question) -> None:
        if q.hypothesis.state is not HypothesisState.REGISTERED:
            raise ValueError("only a REGISTERED question is queued; registration is a human's act")
        self.append(QuestionQueued(q.id, q.to_json()))

    def questions(self) -> list[Question]:
        return [Question.from_json(r["question_json"]) for r in self.records()]


# ---- M8.1 / M8.2: registration through the accountant --------------------------

def from_draft(d: Draft, *, id: str, template: StrategySpec, budget: AlphaBudget, available_n: int,
               instrument_class: InstrumentClass = InstrumentClass.US_LARGE, instrument_currency: str = "USD") -> Question:
    alpha = budget.plan_alpha(d.axis, d.tier, d.search_space_size)
    h = to_hypothesis(d, id=id, available_n=available_n, alpha=alpha)
    if template.axis is not d.axis:
        raise ValueError("the template's axis must be the Draft's")
    return Question(h, template, d.sweep, instrument_class, instrument_currency)


def max_plateau_neighbourhood(sweep: Sweep) -> int:
    """The largest Chebyshev-1 neighbourhood the sweep's geometry can hold —
    the product of min(3, n) over its axes. A declared plateau larger than
    this can never be shown, so the plateau check would refuse every
    winner: a gate that cannot pass is decoration, and alpha spent behind
    it buys nothing (found by Q-004, 2026-09-12: one axis of two values
    against a four-cell plateau)."""
    import math

    return math.prod(min(3, len(v)) for _, v in sweep.axes) if sweep.axes else 0


def register_question(q: Question, *, confirmation: Confirmation, budget: AlphaBudget, register: Register,
                      declared: Consumed | None, parent: Hypothesis | None = None,
                      names: "frozenset[str] | None" = None) -> Question:
    """M8.1: accepted, the axis decremented by rate × k. M8.2: an underpowered
    question is refused here — before it runs and before it spends — and so
    is a pooled set too small for leave-one-out ever to pass."""
    from occams.guards import Refusal, refuse_or_pass
    from occams.guards.leave_one_out import MIN_GROUPS

    h = q.hypothesis
    need = h.required_n
    if names is not None and len(names) < MIN_GROUPS:
        refuse_or_pass(Refusal("DRAFT->REGISTERED", f"unsupportable as pooled: {len(names)} name(s) — leave-one-out needs at least "
                                                    f"{MIN_GROUPS} groups, so no measurement on this set could ever be supported; "
                                                    f"widen the set before registering (ADR-0012)",
                               {"names": sorted(names), "min_groups": MIN_GROUPS}),
                       register, spec_hash=q.template.hash, hypothesis_id=h.id)
    cap = max_plateau_neighbourhood(q.sweep)
    if h.gates.plateau_cells > cap:
        shape = " × ".join(str(len(v)) for _, v in q.sweep.axes) or "empty"
        refuse_or_pass(Refusal("DRAFT->REGISTERED", f"unsupportable sweep: a plateau of {h.gates.plateau_cells} cells cannot fit a "
                                                    f"{shape} sweep, whose largest neighbourhood is {cap}; the plateau check could "
                                                    f"never pass, so no measurement on this sweep could ever be supported",
                               {"plateau_cells": h.gates.plateau_cells, "max_neighbourhood": cap, "sweep": q.sweep.as_dict()}),
                       register, spec_hash=q.template.hash, hypothesis_id=h.id)
    if h.power_plan.available_n < need:
        refuse_or_pass(Refusal("DRAFT->REGISTERED", "underpowered: say so and do not run it — the measurement partition "
                                                    "cannot see the declared floor (M8.2)",
                               {"required_n": need, "available_n": h.power_plan.available_n}),
                       register, spec_hash=q.template.hash, hypothesis_id=h.id)
    h2 = _register_hypothesis(h, confirmation=confirmation, parent=parent, register=register, budget=budget,
                              declared=declared)
    return replace(q, hypothesis=h2)


# ---- M8.3: measure and resolve --------------------------------------------------------

def available_trades(bars: dict[str, Bars], *, trades_per_name_year: float) -> int:
    """The on-paper trade count the plan declares: names × years × frequency."""
    years = max(b.days for b in bars.values()) / 252.0 if bars else 0.0
    return int(len(bars) * years * trades_per_name_year)


def measurement_world(q: Question, *, cfg: Config, archive: BarArchive, register: Register, partition: str = "measurement",
                      window: tuple[int, int] | None = None) -> dict:
    """The bars a question is measured on and everything that goes with
    them: the universe's members on the universe's frozen calendar when the
    question came from a survey (M12.5), else the archive on the Register's
    calendar; the partition's bounds; the pooled actions; the bounded costs;
    the frozen classifier's context when the template is gated; the engine
    the horizon selects (D6)."""
    from occams.engine import day_boxed, position_boxed

    parts = Partitions.from_config(cfg)
    latest = archive.latest_bars()
    if not latest:
        raise Refused((forward.Refusal("REGISTERED->MEASURED", "the archive holds no bars; nothing real has been ingested", {}),))
    from occams.data.partitions import declared_universe, span_for
    universe = str((q.hypothesis.survey or {}).get("universe") or "")
    if universe:   # M12.5: a question from a survey is measured on its universe's members and its universe's frozen calendar
        u = declared_universe(register, universe)
        if u is None:
            raise Refused((forward.Refusal("REGISTERED->MEASURED", f"universe {universe!r} is not declared in this Register", {}),))
        latest = {n: latest[n] for n in u["members"] if n in latest}
    span = span_for(register, {n: b for n, (b, _a) in latest.items()}, parts, universe=universe)  # the frozen calendar (ADR-0038), one for the pooled set
    bounds = parts.bounds_over(*span)[partition]
    if window is not None:                       # M15.9: a roll — a sub-window of the partition, never beyond it
        lo, hi = int(window[0]), int(window[1])
        if not (bounds[0] <= lo < hi <= bounds[1]):
            raise Refused((forward.Refusal("REGISTERED->MEASURED", f"a roll must lie inside the {partition} partition "
                                           f"{bounds}; {(lo, hi)} does not — the reserve is never read (ADR-0006)", {}),))
        bounds = (lo, hi)
    world = {}
    actions = ActionSeries()
    for name, (bars, acts) in latest.items():
        sliced, _b = parts.slice(bars, partition, span=span)
        if window is not None and sliced.n:
            from occams.data.partitions import slice_days
            sliced = slice_days(sliced, *bounds)
        if sliced.n:
            world[name] = sliced
            actions = ActionSeries(actions.actions + acts.actions)
    if not world:
        raise Refused((forward.Refusal("REGISTERED->MEASURED", f"no series has bars in the {partition} partition", {}),))
    costs = EquityCosts.declared(q.instrument_class, instrument_currency=q.instrument_currency,
                                 account_currency=cfg.capital.currency).bound()
    engine = position_boxed if q.template.horizon is Horizon.MULTI_DAY else day_boxed
    regime = None
    if q.template.regime is not None:
        from occams.engine.regime_gate import RegimeContext

        regime = RegimeContext.from_register(register, archive)  # the frozen classifier, or a refusal in the engine
    return {"world": world, "actions": actions, "bounds": bounds, "parts": parts, "costs": costs, "engine": engine,
            "regime": regime, "partition": partition, "universe": universe}


def measure_question(q: Question, *, cfg: Config, archive: BarArchive, register: Register, seed: int,
                     null_draws: int, partition: str = "measurement", window: tuple[int, int] | None = None) -> tuple[Question, Measurement]:
    """Reads the archive's measurement partition; the engine is the one the
    horizon selects; costs are the bounded model in the configured currency.
    ``window`` (M15.9) narrows the partition to a roll inside it."""
    from occams import identity

    identity.require_clean(f"REGISTERED -> MEASURED of {q.id}")     # ADR-0055: dirty or unknown code does not measure
    w = measurement_world(q, cfg=cfg, archive=archive, register=register, partition=partition, window=window)
    m = w["engine"].measure(q.template, q.sweep.as_dict(), apply_cell, w["world"], seed=seed, cost_in_r=0.0,
                            null_draws=null_draws, partition=partition, actions=w["actions"], partition_bounds=w["bounds"],
                            split=w["parts"].as_tuple(), costs=w["costs"], regime=w["regime"])
    m = replace(m, engine_code_sha=identity.own_code_sha())         # the content hash, beside the commit, on every record of it
    h = measure(q.hypothesis, m, register=register)
    return replace(q, hypothesis=h), m


# ---- M12.6: depth — what the verdict does not say by itself -------------------------------------

ERAS = 3


def eras_of(bounds: tuple[int, int], n: int = ERAS) -> list[tuple[int, int]]:
    lo, hi = bounds
    step = (hi - lo) / n
    return [(int(lo + i * step), int(lo + (i + 1) * step) if i < n - 1 else hi) for i in range(n)]


def _mean(xs) -> float | None:
    xs = list(xs)
    return float(sum(xs) / len(xs)) if xs else None


def depth_records(q: Question, m: Measurement, *, cfg: Config, archive: BarArchive, register: Register, seed: int) -> tuple[dict, dict | None]:
    """After a verdict (M12.6): the winner cell's era decomposition on the
    measurement partition with each era held out and the entries the fill
    auditor refused (ADR-0041's verdict-side census), and — for a question
    registered from a survey — the shrinkage from screening: the cell's
    definition EV and margin beside the measured ones at the same geometry
    against always-long. Two records, appended; diagnostics, not gates."""
    from occams.spec.compile import derived_capabilities, to_engine
    from occams.spec.spec import Entry, EntryKind, OrderType, Side

    w = measurement_world(q, cfg=cfg, archive=archive, register=register, partition=m.partition)
    winner = m.winner
    winner_spec = apply_cell(q.template, dict(winner.params))
    engine = w["engine"]
    run_kw = dict(seed=seed, cost_in_r=0.0, actions=w["actions"], costs=w["costs"], regime=w["regime"])
    again = engine.run(to_engine(winner_spec), w["world"], **run_kw)                     # the winner's own run: its missed entries
    missed = tuple(getattr(again, "missed", ()))
    by: dict[str, int] = {}
    for x in missed:
        by[x.name] = by.get(x.name, 0) + 1
    bounds = m.partition_bounds or (min(t.day for t in winner.trades), max(t.day for t in winner.trades) + 1)
    eras = []
    for lo, hi in eras_of(bounds):
        v = [t.net_r for t in winner.trades if lo <= t.day < hi]
        eras.append({"bounds": [lo, hi], "n": len(v), "ev_net": _mean(v)})
    loeo = tuple(_mean(t.net_r for t in winner.trades if not (e["bounds"][0] <= t.day < e["bounds"][1])) for e in eras)
    era_rec = register.EraDecomposition(q.id, winner.spec_hash, m.partition, tuple(eras), loeo, len(missed), dict(sorted(by.items())), seed)
    register.append(era_rec)
    sv = q.hypothesis.survey or {}
    d = sv.get("definition") or {}
    if not sv.get("cell"):
        return _plain(era_rec), None
    base_spec = winner_spec.replace(entries=(Entry(EntryKind.ALWAYS, Side.LONG, ()),), order_type=OrderType.MARKET)
    base_spec = base_spec.replace(required_capabilities=derived_capabilities(base_spec))
    base = engine.run(to_engine(base_spec), w["world"], **run_kw)                          # always-long at the winner's geometry
    base_ev = _mean(t.net_r for t in base)
    measured_ev = float(winner.ev)
    margin = None if base_ev is None else measured_ev - base_ev
    d_ev, d_margin = d.get("ev_net"), d.get("margin_net")
    sh = register.Shrinkage(q.id, str(sv.get("results_sha", "")), str(sv["cell"]), int(sv.get("screened_cells", 0)),
                            int(d.get("trades") or 0), d_ev, d_margin, int(winner.n), measured_ev, base_ev, margin,
                            None if d_ev is None else measured_ev - float(d_ev),
                            None if (d_margin is None or margin is None) else margin - float(d_margin))
    register.append(sh)
    return _plain(era_rec), _plain(sh)


def path_distribution(m: Measurement, *, draws: int, seed: int) -> np.ndarray:
    """D19: the winner's own Monte Carlo *paths* — cumulative net R over
    bootstrapped trade sequences — not a summary. Shape (draws, n)."""
    x = np.asarray([t.net_r for t in m.winner.trades], dtype=float)
    rng = np.random.default_rng([int(seed), 19])
    idx = rng.integers(0, x.size, size=(draws, x.size))
    return np.cumsum(x[idx], axis=1)


def resolve_question(q: Question, m: Measurement, *, register: Register, archive: BarArchive, seed: int,
                     path_draws: int = 2000) -> tuple[Question, Verdict, Strategy | None]:
    """The template measures; the winner trades (ADR-0036)."""
    h = q.hypothesis
    judged = forward.evaluations(m, h)                     # each check once: its refusal or None, and what it saw
    fired = tuple(r for r, _ in judged if r is not None)
    winner = m.winner
    for r in fired:  # N6: every refusal is queryable, with its evidence, not only named in the Verdict
        register.append(register.RefusalRecorded(r.transition, r.reason, dict(r.evidence), winner.spec_hash, h.id))
    for name, (r, seen) in zip(forward.CHECKS, judged):    # M16.8: and every check's numbers, passing or failing, before the resolution
        register.append(register.GuardEvidence(h.id, winner.spec_hash, name, r is None, dict(seen)))
    winner_spec = apply_cell(q.template, dict(winner.params))
    assert winner_spec.hash == winner.spec_hash
    outcome = "supported" if not fired else "null"
    v = Verdict(outcome, winner.ev, winner.n / m.years, winner.spec_hash, m.engine_sha, m.seed, m.partition,
                tuple(r.reason for r in fired), cost_basis=m.cost_basis, family_hash=m.spec_hash,
                winner_cell=tuple(winner.indices), checks=tuple(forward.CHECKS), surface=m.surface,
                engine_code_sha=m.engine_code_sha)
    # the template's Strategy: SPECIFIED -> COMPILED -> MEASURED, and no further
    template_s = Strategy.from_spec(q.template, hypothesis_id=h.id)
    template_s = transition(template_s, StrategyState.COMPILED, register=register)
    template_s = transition(template_s, StrategyState.MEASURED, register=register, measurement=m)
    # M8.5: archive the path distribution before the verdict is recorded
    paths = path_distribution(m, draws=path_draws, seed=seed)
    sha = archive.put_blob("paths", {"hypothesis_id": h.id, "spec_hash": winner.spec_hash, "draws": int(paths.shape[0]),
                                     "trades": int(paths.shape[1]), "paths": [[round(float(x), 6) for x in row] for row in paths]})
    register.append(PathsArchived(h.id, winner.spec_hash, sha, int(paths.shape[0]), int(paths.shape[1])))
    h2 = resolve(h, v, register=register)
    deployable = None
    if outcome == "supported":
        deployable = Strategy.from_spec(winner_spec, hypothesis_id=h.id)
        deployable = transition(deployable, StrategyState.COMPILED, register=register)
        deployable = transition(deployable, StrategyState.MEASURED, register=register, measurement=m)
        deployable = transition(deployable, StrategyState.FORWARD, register=register, hypothesis=h2)
        assert deployable.spec_hash == v.spec_hash
    return replace(q, hypothesis=h2), v, deployable


# ---- M8.4: the implementation child ----------------------------------------------------

def implementation_draft(parent: Hypothesis, winner_spec: StrategySpec, *, proposer: str = "implementation") -> Draft:
    """The child question for the Strategy built on a resolved mechanism:
    does *this* spec clear its floor net of costs and obtainability."""
    return Draft(proposer=proposer, axis=parent.axis,
                 mechanism=f"implementation of {parent.id}: spec {winner_spec.hash[:12]} clears the floor net of "
                           f"costs and obtainability as measured",
                 if_true="the Strategy proceeds to its forward window", if_false="the Strategy is retired; the mechanism stands",
                 falsifier="the winner's EV in net R at or below the floor under the bounded cost model",
                 floor=parent.floor, sweep=Sweep((("stop", (winner_spec.stop.value,)),)),
                 sigma_r=parent.power_plan.sigma_r, sigma_provenance="inherited from the resolved mechanism parent",
                 power=parent.power_plan.power,
                 # one cell is its own neighbourhood: the plateau check on a child can only ask
                 # "lone spike?", which a single cell cannot be. Inheriting the parent's plateau_cells
                 # made every implementation child unpassable at MEASURED -> FORWARD (found 2026-09-12
                 # by max_plateau_neighbourhood, before any child had been registered).
                 gates=replace(parent.gates, plateau_cells=1), tier=Tier.IMPLEMENTATION, parent_id=parent.id)


# ---- the author-facing command: prepare, then register ---------------------------------

def main(argv=None) -> int:
    """``python -m occams question prepare|register`` — DRAFT-003 from the
    frozen classifier. ``prepare`` shows every number registration would
    use and spends nothing; ``register --by NAME --yes`` is the human act:
    it spends alpha and queues the question for the loop."""
    import argparse
    from pathlib import Path

    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("prepare", "register") and "--from-survey" in argv:   # M12.5: from a recorded survey
        from occams.survey.candidates import register_main

        return register_main(argv)
    if argv and argv[0] == "remeasure":                                           # M15.9: a resolved question on a rolling cut
        from occams.rolls import main as remeasure_main

        return remeasure_main(argv[1:])

    from occams.config import load
    from occams.data.archive import BarArchive
    from occams.hypothesis import Confirmation
    from occams.ledger.alpha_budget import AlphaBudget
    from occams.proposers.regime import RegimeProposer, frozen, precommit, template_for
    from occams.spec.spec import Regime
    from occams.whatif import config_sha

    ap = argparse.ArgumentParser(prog="python -m occams question")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("prepare", "register"):
        p = sub.add_parser(name)
        p.add_argument("--archive", required=True, type=Path)
        p.add_argument("--register", required=True, type=Path)
        p.add_argument("--queue", type=Path)
        p.add_argument("--config", default=None, help="the programme's config; default: the working directory's occams.toml")
        p.add_argument("--id", default="Q-003")
        p.add_argument("--axis", choices=("regime", "price_daily"), default="regime")
        p.add_argument("--regime", choices=[r.value for r in Regime], default="up", help="regime axis: the gate's label")
        p.add_argument("--entry", choices=("close_below_ma", "close_above_ma", "breakout_high",
                                           "down_run", "return_below", "pullback_in_trend"), default="close_below_ma",
                       help="price_daily axis: the entry kind (the last three by ADR-0037)")
        p.add_argument("--lookback", type=int, default=None, help="price_daily axis: lookback in bars (the average, breakout and return_below kinds)")
        p.add_argument("--runs", type=int, default=None, help="down_run: consecutive lower closes")
        p.add_argument("--percent", type=float, default=None, help="return_below: the decline in percent over --lookback")
        p.add_argument("--short", type=int, default=None, help="pullback_in_trend: the short average's bars")
        p.add_argument("--long", type=int, default=None, help="pullback_in_trend: the long average's bars")
        p.add_argument("--hold", type=int, default=None, help="price_daily axis: the time exit in bars (required)")
        p.add_argument("--holds", default="", help="price_daily axis: comma list to sweep the hold as an axis")
        p.add_argument("--horizon", choices=("multi_day", "intraday"), default="multi_day", help="price_daily axis: the engine (D6)")
        p.add_argument("--floor-ev", type=float, required=True, help="the declared floor, EV per trade in net R")
        p.add_argument("--floor-frequency", type=float, required=True, help="the declared floor, trades per year")
        p.add_argument("--sigma", type=float, required=True, help="declared sigma of R per trade, with --sigma-provenance")
        p.add_argument("--sigma-provenance", required=True)
        p.add_argument("--power", type=float, default=0.8)
        p.add_argument("--stops", default="2,3")
        p.add_argument("--targets", default=None, help="regime axis: target multiples; empty for none (default 2,3 on regime, none on price_daily)")
        p.add_argument("--supersedes", default=None, help="the resolved question this one supersedes (R4.9)")
        p.add_argument("--distinction", default=None, help="the stated difference from an overlapping resolved question (R4.9)")
        p.add_argument("--plateau-cells", type=int, default=4)
        p.add_argument("--plateau-slack", type=float, default=0.10)
        p.add_argument("--loo-min-fraction", type=float, default=0.5)
        p.add_argument("--seed", type=int, default=1)
        if name == "register":
            p.add_argument("--by", required=True)
            p.add_argument("--yes", action="store_true", help="the human confirmation; without it nothing is registered")
    a = ap.parse_args(argv)
    cfg = load(a.config)
    reg = Register(a.register)
    archive = BarArchive(a.archive)
    from occams.stopping import describe, stopping_record

    stop = stopping_record(reg)
    if stop:   # ADR-0033, M12.8: any of the three stopping conditions is terminal for this Register
        head = "LAB CLOSED (ADR-0033)" if stop["type"] == "LabClosed" else "PROGRAMME STOPPED (M12.8)"
        print(f"{head}: {describe(stop)}; nothing prepares or registers after that record. A new question is a new programme.")
        return 1
    from occams.proposers.price import PriceProposer, price_template
    from occams.spec.spec import EntryKind, Horizon
    clf = index_name = None
    if a.axis == "regime":
        clf = frozen(reg)
        if clf is None:
            print("REFUSED: no classifier is frozen in this Register (ADR-0005) — run `python -m occams classifier freeze` first")
            return 1
        index_name = [r for r in reg.records() if r["type"] == "ClassifierFrozen"][-1]["index_name"]
        template = template_for(clf, label=Regime(a.regime), index_name=index_name)
    else:
        if a.hold is None:
            print("REFUSED: a price_daily question declares its --hold; there is no default for a mechanism's parameters")
            return 2
        entry_kw = dict(lookback=a.lookback, runs=a.runs, percent=a.percent, short=a.short, long=a.long)
        try:
            template = price_template(EntryKind(a.entry), hold_bars=a.hold, horizon=Horizon(a.horizon), **entry_kw)
        except ValueError as e:
            print(f"REFUSED: {e}")
            return 2
    targets = a.targets if a.targets is not None else ("2,3" if a.axis == "regime" else "")
    axes = [("stop", tuple(float(x) for x in a.stops.split(",")))]
    if targets.strip():
        axes.append(("target", tuple(float(x) for x in targets.split(","))))
    if a.holds.strip():
        axes.append(("hold", tuple(float(x) for x in a.holds.split(","))))
    sweep = Sweep(tuple(axes))
    budget = AlphaBudget(cfg, reg, config_sha=config_sha(cfg))
    pre = precommit(template, archive=archive, cfg=cfg, register=reg, seed=a.seed, sweep=sweep)   # M13.9: the thinnest cell bounds the promise
    from occams.proposers.regime import axis_sensitivity
    sens = axis_sensitivity(template, sweep, pre["definition_bars"], ctx=pre["context"], seed=a.seed)
    inert = [ax for ax, v in sens.items() if v == 0.0]
    gates = Gates(a.plateau_cells, a.plateau_slack, a.loo_min_fraction)
    from occams.proposers.base import DraftQueue, Sandbox
    sb = Sandbox.build(reg, DraftQueue(Path(a.queue or a.register).with_name("drafts.jsonl")))
    if a.axis == "regime":
        proposer = RegimeProposer(clf, floor=Floor(a.floor_ev, a.floor_frequency), sigma_r=a.sigma,
                                  sigma_provenance=a.sigma_provenance, power=a.power, gates=gates, sweep=sweep)
        (draft,) = proposer.propose(sb, Regime(a.regime))
    else:
        proposer = PriceProposer(entry=EntryKind(a.entry), hold_bars=a.hold,
                                 floor=Floor(a.floor_ev, a.floor_frequency), sigma_r=a.sigma,
                                 sigma_provenance=a.sigma_provenance, power=a.power, gates=gates, sweep=sweep, **entry_kw)
        (draft,) = proposer.propose(sb)
    q = from_draft(draft, id=a.id, template=template, budget=budget, available_n=pre["available_n"])
    if pre["clustering"] is not None:
        q = replace(q, hypothesis=replace(q.hypothesis, power_plan=q.hypothesis.power_plan.with_clustering(pre["clustering"])))
    q = replace(q, hypothesis=replace(q.hypothesis, supersedes=a.supersedes, distinction=a.distinction))
    h = q.hypothesis
    lo, hi = pre["measurement_bounds"]
    declared = Consumed(a.id, h.axis, "measurement", lo, hi, frozenset(pre["names"]))
    from occams.ledger.alpha_budget import SearchBudget
    overlap_refusal = SearchBudget(reg).gate(declared, threshold=cfg.lab.overlap_threshold, supersedes=h.supersedes,
                                            distinction=h.distinction)
    where = (f"in the {a.regime} regime of {clf.frozen_hash[:12]} (index {index_name})" if clf is not None else
             ", ".join(f"{k} {v:g}" for k, v in template.entries[0].params) + f", hold {a.hold} bars, {a.horizon}, no regime gate")
    print(f"question {a.id} on {h.axis.value}: {template.entries[0].kind.value} {where}; "
          f"template {template.hash[:12]}; sweep {sweep.as_dict()} -> k = {h.search_space_size}")
    print(f"pre-committed on the definition partition ({pre['definition_days']} days): {pre['definition_trades']} signals, "
          f"rate {pre['rate_per_name_day']:.4f} per name-day; measurement {pre['measurement_days']} days over {pre['names']}")
    if pre.get("baseline_trades") and pre.get("definition_ev_net") is not None and pre.get("baseline_ev_net") is not None:
        print(f"always-long at the template's geometry and gate on the definition partition: EV {pre['baseline_ev_net']:+.3f} net R over "
              f"{pre['baseline_trades']} trades; the template's signals EV {pre['definition_ev_net']:+.3f}; margin "
              f"{pre['definition_ev_net'] - pre['baseline_ev_net']:+.3f} — the fifth check (ADR-0043) asks the same at the corrected alpha "
              f"on the measurement partition")
    print(f"available_n {pre['available_n']}" + (f" -> effective {h.power_plan.available_n} at measured rho {h.power_plan.rho:.3f}" if h.power_plan.rho is not None else " (clustering not measurable on the definition signals)"))
    if pre.get("thinnest_cell"):
        tc = pre["thinnest_cell"]
        geom = ", ".join(f"{k} {v:g}" for k, v in tc["point"].items())
        print(f"the sweep's thinnest cell on the definition partition: {geom} — {tc['definition_trades']} trades, ≈{tc['available_n']} on the "
              f"measurement partition, against {pre['template_available_n']} from the template's signals; available_n is the lesser, because "
              f"the guard at measurement counts the winner's own trades (M8.2, M13.9)")
    print(f"required_n per cell {h.required_n} at per-cell alpha {budget.rate(h.axis, h.tier):.4g}; spend {budget.spend_for(h.axis, h.tier, h.search_space_size):.4g} "
          f"of {budget.remaining(h.axis):.4g} remaining on {h.axis.value}")
    from occams.guards.leave_one_out import MIN_GROUPS
    powered = h.power_plan.available_n >= h.required_n
    supportable = len(pre["names"]) >= MIN_GROUPS
    print("POWERED" if powered else "UNDERPOWERED — registration would be refused (M8.2)")
    if not supportable:
        print(f"UNSUPPORTABLE — {len(pre['names'])} name(s); leave-one-out needs {MIN_GROUPS}, so no verdict on this set could be supported; registration would be refused")
    cap = max_plateau_neighbourhood(sweep)
    plateau_ok = h.gates.plateau_cells <= cap
    if not plateau_ok:
        print(f"UNSUPPORTABLE — a plateau of {h.gates.plateau_cells} cells cannot fit this sweep (largest neighbourhood {cap}); "
              f"the plateau check could never pass; lower --plateau-cells or widen the sweep; registration would be refused")
    print("axis sensitivity on the definition partition (share of trades that change along the axis): "
          + ", ".join(f"{ax} {v:.1%}" for ax, v in sens.items()))
    from occams.proposers.regime import definition_surface
    surf = definition_surface(template, sweep, pre["definition_bars"], ctx=pre["context"], seed=a.seed)
    if surf:
        by_margin, by_ev = surf[0], max(surf, key=lambda r: r["ev"])
        print(f"on the definition partition the sweep's winner by margin over always-long (ADR-0045) is "
              f"{by_margin['params']}: EV {by_margin['ev']:+.3f}, always-long {by_margin['baseline_ev']:+.3f}, margin "
              f"{by_margin['margin']:+.3f} over {by_margin['n']} trades; by EV it would be {by_ev['params']} (EV {by_ev['ev']:+.3f}, "
              f"margin {by_ev['margin']:+.3f})")
    if inert:
        print(f"INERT AXIS — {inert}: every cell along it produces the same trades on the definition partition; "
              f"k = {h.search_space_size} charges for cells that are not distinct questions. Drop the axis or change the horizon")
    if overlap_refusal is not None:
        print(f"OVERLAP — {overlap_refusal.reason}")
    clean = powered and supportable and plateau_ok and not inert and overlap_refusal is None
    if a.cmd == "prepare":
        print("nothing registered, nothing spent.")
        return 0 if clean else 1
    if not clean:
        print("REFUSED: prepare is not clean; registration would spend alpha on a question the gates already answer")
        return 1
    if not a.yes:
        print("REFUSED: registration is a human act; pass --yes to confirm (R4.8)")
        return 2
    try:
        q = register_question(q, confirmation=Confirmation(a.by, human=True), budget=budget, register=reg,
                              declared=declared, names=frozenset(pre["names"]))
    except Refused as e:
        print(f"REFUSED: {e}")
        return 1
    queue = QuestionQueue(a.queue or a.register.with_name("queue.jsonl"))
    queue.enqueue(q)
    print(f"REGISTERED {a.id} by {a.by}: alpha spent {q.hypothesis.alpha_spent:.4g}; queued at {queue.path}. "
          f"Next: python -m occams loop {a.register} {a.archive} {queue.path}")
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
