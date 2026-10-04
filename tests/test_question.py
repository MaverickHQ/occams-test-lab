"""M8.1-M8.5 — the first question, end to end on synthetic bars through the
real archive. The first *real* verdict waits only for real bars."""

from __future__ import annotations

import copy
from pathlib import Path

import numpy as np
import pytest

from occams.config import InformationAxis, parse
from occams.data.actions import ActionSeries
from occams.data.archive import BarArchive
from occams.data.bars import Bars, random_walk
from occams.guards import Refused
from dataclasses import replace

from occams.hypothesis import Confirmation, Gates, HypothesisState, Tier
from occams.ledger.alpha_budget import AlphaBudget, Consumed
from occams.measurement import Floor
from occams.proposers.base import Draft, Sweep
from occams.question import (QuestionQueue, apply_cell, available_trades, from_draft, implementation_draft,
                             measure_question, register_question, resolve_question)
from occams.register import Register
from occams.spec import (Capability, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType, Side, Sizing, Stop,
                         StopKind, StrategySpec, UniverseRule)
from occams.strategy import StrategyState
from tests.test_config import FIXTURE
from tests.test_whatif import AFFORDABLE_AXES

HUMAN = Confirmation("author", True)
CAPS = frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS})


def cfg():
    raw = copy.deepcopy(FIXTURE)
    raw["capital"]["currency"] = "USD"
    raw["alpha"]["axes"] = copy.deepcopy(AFFORDABLE_AXES)  # regime 0.5 @ 0.1/0.05 — a 4-cell question costs 0.4
    raw["lab"]["overlap_threshold"] = 0.9
    return parse(raw, Path("fixture"))


def template(axis=InformationAxis.REGIME):
    return StrategySpec(entries=(Entry(EntryKind.ALWAYS, Side.LONG),), exits=(Exit(ExitKind.TIME, (("bars", 1),)),),
                        stop=Stop(StopKind.PERCENT, 3.0), sizing=Sizing(), order_type=OrderType.MARKET,
                        horizon=Horizon.INTRADAY, universe=UniverseRule((("world", "synthetic"),)),
                        required_capabilities=CAPS, axis=axis)


def draft(sweep=Sweep((("stop", (2.0, 3.0)), ("target", (3.0, 4.0)))), floor=Floor(0.15, 20)):
    return Draft(proposer="t", axis=InformationAxis.REGIME, mechanism="continuation after the open", if_true="t",
                 if_false="f", falsifier="x", floor=floor, sweep=sweep, sigma_r=1.2, sigma_provenance="fixture",
                 power=0.8, gates=Gates(2, 0.30, 0.5, 50.0), alternative_ev_net_r=floor.ev_net_r + 0.30)


def world_archive(tmp_path, *, drift: float, days=600, names=("A", "B", "C")) -> BarArchive:
    arch = BarArchive(tmp_path / "archive")
    for i, n in enumerate(names):
        arch.put(random_walk(n, days=days, seed=10 + i, sigma_daily=0.02, drift_daily=drift), ActionSeries(), source_id="synthetic")
    return arch


def edge_template(axis=InformationAxis.REGIME):
    """ADR-0043: a supported verdict needs an entry with something to find, not
    a drift always-long would ride — after two lower closes, long at the open."""
    return template(axis).replace(entries=(Entry(EntryKind.DOWN_RUN, Side.LONG, (("runs", 2),)),))


def edge_bars(name: str, *, days: int, seed: int, up: float = 0.015, noise: float = 0.004, walk: float = 0.012,
              range_fraction: float = 0.005) -> Bars:
    """A walk with a reversal to find: the day after two lower closes is up by
    ``up``; every other day is driftless noise. Intraday ranges are narrow, so
    a 2–3 % stop rarely bites and the entry's edge reaches the verdict.
    Always-long catches the same up-days one day in four; the down-run
    catches every one — the margin the fifth check (ADR-0043) measures."""
    rng = np.random.default_rng(seed)
    o, h, lo, c = [], [], [], []
    close = 100.0
    for _ in range(days):
        z, u = rng.standard_normal(), abs(rng.standard_normal())
        r = up + noise * z if len(c) >= 3 and c[-1] < c[-2] < c[-3] else walk * z
        op = close
        close = close * float(np.exp(r))
        o.append(op)
        c.append(close)
        h.append(max(op, close) * (1 + range_fraction * u))
        lo.append(min(op, close) * (1 - range_fraction * u))
    return Bars(name, tuple(o), tuple(h), tuple(lo), tuple(c), tuple(1e6 for _ in o), tuple(range(days)))


def reverting_world(tmp_path, days=2400, names=("A", "B", "C")) -> BarArchive:
    """The world a supported verdict needs under the fifth check: the down-run
    has a margin over always-long. Long enough that an entry firing on a
    quarter of the days meets the power plan on the measurement partition."""
    arch = BarArchive(tmp_path / "archive")
    for i, n in enumerate(names):
        arch.put(edge_bars(n, days=days, seed=10 + i), ActionSeries(), source_id="synthetic")
    return arch


@pytest.fixture
def lab(tmp_path):
    reg = Register(tmp_path / "r.jsonl")
    c = cfg()
    return c, reg, AlphaBudget(c, reg, config_sha="fixture")


def test_apply_cell_edits_the_template_and_refuses_unknown_axes():
    t = template()
    s = apply_cell(t, {"stop": 2.0, "target": 3.0, "hold": 2.0})
    assert s.stop.value == 2.0 and any(x.kind is ExitKind.TARGET_R for x in s.exits)
    assert next(x for x in s.exits if x.kind is ExitKind.TIME).param("bars") == 2.0
    with pytest.raises(ValueError, match="sweep axis"):
        apply_cell(t, {"leverage": 2.0})


def test_m8_1_the_first_mechanism_hypothesis_registers_and_the_axis_is_decremented(lab):
    c, reg, budget = lab
    q = from_draft(draft(), id="Q-1", template=template(), budget=budget, available_n=900)
    q = register_question(q, confirmation=HUMAN, budget=budget, register=reg,
                          declared=Consumed("Q-1", InformationAxis.REGIME, "measurement", 150, 450, frozenset("ABC")))
    assert q.hypothesis.state is HypothesisState.REGISTERED
    assert q.hypothesis.alpha_spent == pytest.approx(0.1 * 4) and budget.remaining(InformationAxis.REGIME) == pytest.approx(0.1)
    assert q.hypothesis.power_plan.alpha == pytest.approx(0.4)  # rate x k: per-cell alpha is the rate


def test_m8_2_an_underpowered_question_is_refused_at_registration_and_spends_nothing(lab):
    c, reg, budget = lab
    q = from_draft(draft(), id="Q-weak", template=template(), budget=budget, available_n=40)
    with pytest.raises(Refused, match="underpowered"):
        register_question(q, confirmation=HUMAN, budget=budget, register=reg, declared=None)
    assert budget.remaining(InformationAxis.REGIME) == pytest.approx(0.5)
    assert reg.records()[-1]["type"] == "RefusalRecorded"


def _registered(lab, tmp_path, drift, floor=Floor(0.15, 20), *, edge: bool = False):
    """``edge``: the reverting world and the down-run template — what a supported verdict needs under the fifth check."""
    c, reg, budget = lab
    arch = reverting_world(tmp_path) if edge else world_archive(tmp_path, drift=drift)
    bars = {n: b for n, (b, _) in arch.latest_bars().items()}
    q = from_draft(draft(floor=floor), id="Q-1", template=edge_template() if edge else template(), budget=budget,
                   available_n=available_trades(bars, trades_per_name_year=252 * 0.5))
    q = register_question(q, confirmation=HUMAN, budget=budget, register=reg, declared=None)
    return c, reg, budget, arch, q


def test_m8_3_a_supported_verdict_freezes_the_winner_and_the_winner_trades(lab, tmp_path):
    c, reg, budget, arch, q = _registered(lab, tmp_path, drift=0.0, edge=True)
    q, m = measure_question(q, cfg=c, archive=arch, register=reg, seed=3, null_draws=400)
    assert m.partition == "measurement" and m.partition_bounds == (600, 1800) and m.cost_basis == "bounded"
    q, v, deployable = resolve_question(q, m, register=reg, archive=arch, seed=3, path_draws=200)
    assert v.outcome == "supported" and v.refusals == () and len(v.checks) == 5
    assert v.spec_hash == m.winner.spec_hash != q.template.hash and v.family_hash == q.template.hash
    assert deployable is not None and deployable.state is StrategyState.FORWARD and deployable.spec_hash == v.spec_hash
    rec = [r for r in reg.records() if r["type"] == "HypothesisResolved"][-1]
    assert rec["engine_sha"] and rec["seed"] == 3 and rec["partition"] == "measurement" and rec["family_hash"] == q.template.hash
    # the template's Strategy stopped at MEASURED; only the winner's entered FORWARD (ADR-0036)
    moves = [(r["spec_hash"], r["to_state"]) for r in reg.records() if r["type"] == "StrategyTransitioned"]
    assert (q.template.hash, "FORWARD") not in moves and (v.spec_hash, "FORWARD") in moves


def test_m8_3_a_null_verdict_names_its_refusals_and_nothing_trades(lab, tmp_path):
    c, reg, budget, arch, q = _registered(lab, tmp_path, drift=0.0)
    q, m = measure_question(q, cfg=c, archive=arch, register=reg, seed=4, null_draws=400)
    q, v, deployable = resolve_question(q, m, register=reg, archive=arch, seed=4, path_draws=100)
    assert v.outcome == "null" and any(r.startswith("floor") or r.startswith("beats-null") for r in v.refusals)
    assert deployable is None and q.hypothesis.state is HypothesisState.RESOLVED
    assert v.spec_hash == m.winner.spec_hash  # a null verdict freezes the closest cell too


def test_m8_4_the_implementation_child_needs_the_resolved_parent_and_spends_from_its_axis(lab, tmp_path):
    c, reg, budget, arch, q = _registered(lab, tmp_path, drift=0.0, edge=True)
    q, m = measure_question(q, cfg=c, archive=arch, register=reg, seed=3, null_draws=400)
    unresolved_child = implementation_draft(q.hypothesis, apply_cell(q.template, dict(m.winner.params)))
    cq = from_draft(unresolved_child, id="Q-1-impl", template=template(), budget=budget, available_n=900)
    with pytest.raises(Refused, match="not resolved"):
        register_question(cq, confirmation=HUMAN, budget=budget, register=reg, declared=None, parent=q.hypothesis)
    q, v, _ = resolve_question(q, m, register=reg, archive=arch, seed=3, path_draws=100)
    cq = from_draft(implementation_draft(q.hypothesis, apply_cell(q.template, dict(m.winner.params))),
                    id="Q-1-impl", template=template(), budget=budget, available_n=900)
    cq = register_question(cq, confirmation=HUMAN, budget=budget, register=reg, declared=None, parent=q.hypothesis)
    assert cq.hypothesis.tier is Tier.IMPLEMENTATION and cq.hypothesis.alpha_spent == pytest.approx(0.05 * 1)
    assert budget.remaining(InformationAxis.REGIME) == pytest.approx(0.5 - 0.4 - 0.05)
    # a second child spends the last 0.05; a third exceeds what remains (R4.10)
    cq2 = from_draft(implementation_draft(q.hypothesis, apply_cell(q.template, dict(m.winner.params))),
                     id="Q-1-impl-2", template=template(), budget=budget, available_n=900)
    register_question(cq2, confirmation=HUMAN, budget=budget, register=reg, declared=None, parent=q.hypothesis)
    assert budget.remaining(InformationAxis.REGIME) == pytest.approx(0.0)
    cq3 = from_draft(implementation_draft(q.hypothesis, apply_cell(q.template, dict(m.winner.params))),
                     id="Q-1-impl-3", template=template(), budget=budget, available_n=900)
    with pytest.raises(Refused, match="AXIS_BUDGET_EXHAUSTED"):
        register_question(cq3, confirmation=HUMAN, budget=budget, register=reg, declared=None, parent=q.hypothesis)


def test_m8_5_the_path_distribution_is_archived_not_just_the_summary(lab, tmp_path):
    # the drift world: a null verdict under the fifth check, and the paths are archived on any verdict — with drawdowns in them
    c, reg, budget, arch, q = _registered(lab, tmp_path, drift=0.012)
    q, m = measure_question(q, cfg=c, archive=arch, register=reg, seed=3, null_draws=300)
    q, v, _ = resolve_question(q, m, register=reg, archive=arch, seed=3, path_draws=150)
    rec = [r for r in reg.records() if r["type"] == "PathsArchived"][-1]
    blob = arch.get_blob("paths", rec["sha"])
    paths = np.asarray(blob["paths"])
    assert paths.shape == (150, m.winner.n) and rec["spec_hash"] == v.spec_hash
    # a retirement rule can be derived from it later (D19): e.g. the 95th percentile of max drawdown in R
    peak = np.maximum.accumulate(np.maximum(paths, 0), axis=1)
    dd95 = float(np.quantile((peak - paths).max(axis=1), 0.95))
    assert dd95 > 0


def test_an_empty_archive_cannot_measure(lab, tmp_path):
    c, reg, budget = lab
    q = from_draft(draft(), id="Q-1", template=template(), budget=budget, available_n=900)
    q = register_question(q, confirmation=HUMAN, budget=budget, register=reg, declared=None)
    with pytest.raises(Refused, match="no bars"):
        measure_question(q, cfg=c, archive=BarArchive(tmp_path / "empty"), register=reg, seed=1, null_draws=10)


def test_a_question_round_trips_through_the_queue(lab, tmp_path):
    c, reg, budget = lab
    q = from_draft(draft(), id="Q-1", template=template(), budget=budget, available_n=900)
    queue = QuestionQueue(tmp_path / "q.jsonl")
    with pytest.raises(ValueError, match="REGISTERED"):
        queue.enqueue(q)
    q = register_question(q, confirmation=HUMAN, budget=budget, register=reg, declared=None)
    queue.enqueue(q)
    back = queue.questions()[0]
    assert back.hypothesis == q.hypothesis and back.template == q.template and back.sweep == q.sweep


def test_a_pooled_set_too_small_for_leave_one_out_is_refused_at_registration(lab):
    """Two names can never pass leave-one-out, so a question over them can
    never be supported; registering it would spend alpha on a foregone
    conclusion. Found by Q-003 on 2026-09-11, which was exactly that."""
    c, reg, budget = lab
    q = from_draft(draft(), id="Q-2", template=template(), budget=budget, available_n=900)
    with pytest.raises(Refused, match="unsupportable as pooled"):
        register_question(q, confirmation=HUMAN, budget=budget, register=reg, declared=None, names=frozenset({"SPY", "QQQ"}))
    assert budget.remaining(InformationAxis.REGIME) == pytest.approx(0.5)  # nothing spent
    ok = register_question(q, confirmation=HUMAN, budget=budget, register=reg, declared=None, names=frozenset({"A", "B", "C"}))
    assert ok.hypothesis.state is HypothesisState.REGISTERED


def test_fired_refusals_are_recorded_with_evidence_at_resolution(lab, tmp_path):
    c, reg, budget, arch, q = _registered(lab, tmp_path, drift=0.0)
    q, m = measure_question(q, cfg=c, archive=arch, register=reg, seed=4, null_draws=400)
    q, v, _ = resolve_question(q, m, register=reg, archive=arch, seed=4, path_draws=50)
    recorded = [r for r in reg.records() if r["type"] == "RefusalRecorded" and r["hypothesis_id"] == "Q-1"]
    assert {r["reason"] for r in recorded} == set(v.refusals) and all(r["evidence"] for r in recorded)


def test_an_inert_sweep_axis_is_detected_on_the_definition_partition(tmp_path):
    """A target that a one-bar box can never reach changes no trade: the
    axis is inert and would be charged for as if it were a search."""
    from occams.data.bars import random_walk
    from occams.proposers.regime import inert_axes
    world = {n: random_walk(n, days=300, seed=s, sigma_daily=0.02) for n, s in (("A", 1), ("B", 2), ("C", 3))}
    t = template()  # ALWAYS-long market entry, one-bar box
    # 50R and 60R on a 3% stop are a 150% intraday move: unreachable on this data, so the cells coincide
    assert inert_axes(t, Sweep((("stop", (2.0, 3.0)), ("target", (50.0, 60.0)))), world, ctx=None, seed=1) == ["target"]
    assert inert_axes(t, Sweep((("stop", (2.0, 3.0)),)), world, ctx=None, seed=1) == []
    # inertness is a fact about the data and the cells, not the axis name: a 3% stop changes trades a 2% one does not
    from occams.proposers.regime import axis_sensitivity
    sens = axis_sensitivity(t, Sweep((("stop", (2.0, 3.0)), ("target", (50.0, 60.0)))), world, ctx=None, seed=1)
    assert sens["target"] == 0.0 and 0.0 < sens["stop"] < 1.0


def test_a_plateau_the_sweep_cannot_hold_is_refused_at_registration_and_spends_nothing(lab):
    """Q-004, 2026-09-12: one axis of two values against a four-cell plateau
    — a check that could never pass. Refused before any alpha moves."""
    from occams.question import max_plateau_neighbourhood
    c, reg, budget = lab
    assert max_plateau_neighbourhood(Sweep((("stop", (2.0, 3.0)),))) == 2
    assert max_plateau_neighbourhood(Sweep((("stop", (2.0, 3.0)), ("target", (2.0, 3.0))))) == 4
    assert max_plateau_neighbourhood(Sweep((("stop", (1.0, 2.0, 3.0, 4.0)), ("hold", (1.0, 2.0, 3.0))))) == 9
    narrow = draft(sweep=Sweep((("stop", (2.0, 3.0)),)))
    narrow = replace(narrow, gates=Gates(4, 0.30, 0.5, 50.0))
    q = from_draft(narrow, id="Q-narrow", template=template(), budget=budget, available_n=900)
    with pytest.raises(Refused, match="plateau of 4 cells cannot fit a 2 sweep"):
        register_question(q, confirmation=HUMAN, budget=budget, register=reg, declared=None)
    assert budget.remaining(InformationAxis.REGIME) == pytest.approx(0.5)
    assert reg.records()[-1]["type"] == "RefusalRecorded"
    wide = replace(draft(), gates=Gates(4, 0.30, 0.5, 50.0))     # 2 x 2 holds exactly four
    q = from_draft(wide, id="Q-wide", template=template(), budget=budget, available_n=900)
    assert register_question(q, confirmation=HUMAN, budget=budget, register=reg, declared=None).hypothesis.state is HypothesisState.REGISTERED
