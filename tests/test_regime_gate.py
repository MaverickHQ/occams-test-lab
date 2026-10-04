"""The regime gate: identity (ADR-0007), the engine's refusals, causal
admission, the gated null, the forward runner, and the question pipeline
reading the frozen classifier from the Register."""

from __future__ import annotations

import copy
from datetime import datetime, UTC
from pathlib import Path

import pytest

from occams.config import InformationAxis, parse
from occams.data.actions import ActionSeries
from occams.data.archive import BarArchive
from occams.data.bars import Bars, random_walk
from occams.engine import day_boxed, position_boxed
from occams.engine.regime_gate import GateRefusal, RegimeContext, admits
from occams.proposers.regime import ClusterLevel, RegimeClassifier, freeze
from occams.register import Money, Operations, Register
from occams.spec import (Capability, CompileError, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType, Regime,
                         RegimeGate, Side, Sizing, Stop, StopKind, StrategySpec, UniverseRule, to_engine)
from tests.test_config import FIXTURE

CAPS = frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS})
CLF = RegimeClassifier(10, 50, 0.0, ClusterLevel.INDEX)


def spec(gate=RegimeGate(CLF.frozen_hash, Regime.UP, "IDX"), axis=InformationAxis.REGIME, **kw):
    base = dict(entries=(Entry(EntryKind.ALWAYS, Side.LONG),), exits=(Exit(ExitKind.TIME, (("bars", 1),)),),
                stop=Stop(StopKind.PERCENT, 2.0), sizing=Sizing(), order_type=OrderType.MARKET, horizon=Horizon.INTRADAY,
                universe=UniverseRule((("world", "synthetic"),)), required_capabilities=CAPS, axis=axis, regime=gate)
    base.update(kw)
    return StrategySpec(**base)


def world():
    idx = random_walk("IDX", days=400, seed=1, sigma_daily=0.015)
    a = random_walk("A", days=400, seed=2, sigma_daily=0.02)
    return idx, {"A": a, "IDX": idx}


def test_the_gate_is_identity():
    g = spec()
    assert g.hash != spec(gate=None).hash
    assert g.hash != spec(gate=RegimeGate(CLF.frozen_hash, Regime.DOWN, "IDX")).hash
    assert g.hash != spec(gate=RegimeGate("otherhash", Regime.UP, "IDX")).hash
    assert StrategySpec.from_json(g.to_json()) == g and g.identity()["regime"]["label"] == "up"


def test_a_gate_off_the_regime_axis_fails_to_compile():
    with pytest.raises(CompileError, match="regime axis"):
        to_engine(spec(axis=InformationAxis.PRICE_DAILY))
    with pytest.raises(ValueError, match="names the frozen classifier"):
        RegimeGate(" ", Regime.UP, "IDX")


def test_the_engine_refuses_a_gated_spec_without_its_classifier_or_with_the_wrong_one():
    idx, w = world()
    with pytest.raises(GateRefusal, match="without the frozen classifier"):
        day_boxed.run(to_engine(spec()), w, seed=0)
    wrong = RegimeContext(RegimeClassifier(20, 100, 0.01, ClusterLevel.INDEX), "IDX", idx)
    with pytest.raises(GateRefusal, match="D2"):
        day_boxed.run(to_engine(spec()), w, seed=0, regime=wrong)
    with pytest.raises(GateRefusal, match="index level"):
        day_boxed.run(to_engine(spec()), w, seed=0, regime=RegimeContext(CLF, "OTHER", idx))


def test_a_gated_run_trades_only_on_boxes_the_classifier_labels_with_its_regime():
    idx, w = world()
    ctx = RegimeContext(CLF, "IDX", idx)
    labels = CLF.labels(idx)
    trades = day_boxed.run(to_engine(spec()), {"A": w["A"]}, seed=0, regime=ctx)
    assert trades and all(labels[t.day] is Regime.UP for t in trades)
    ungated = day_boxed.run(to_engine(spec(gate=None, axis=InformationAxis.PRICE_DAILY)), {"A": w["A"]}, seed=0)
    assert len(trades) == sum(1 for t in ungated if labels[t.day] is Regime.UP)
    down = day_boxed.run(to_engine(spec(gate=RegimeGate(CLF.frozen_hash, Regime.DOWN, "IDX"))), {"A": w["A"]}, seed=0, regime=ctx)
    assert all(labels[t.day] is Regime.DOWN for t in down) and len(down) + len(trades) < len(ungated)


def test_admission_is_causal():
    idx, w = world()
    ctx = RegimeContext(CLF, "IDX", idx)
    for first in (60, 120, 200, 333):
        before = admits(spec().regime, ctx, w["A"], first)
        f = lambda seq, first=first: tuple(v * 1.4 if i >= first else v for i, v in enumerate(seq))  # noqa: E731
        bumped = Bars("IDX", f(idx.open), f(idx.high), f(idx.low), f(idx.close), idx.volume, idx.day)
        assert admits(spec().regime, RegimeContext(CLF, "IDX", bumped), w["A"], first) == before


def test_the_null_is_drawn_from_the_same_gated_boxes():
    idx, w = world()
    ctx = RegimeContext(CLF, "IDX", idx)
    longs, shorts = day_boxed.box_outcomes(to_engine(spec()), {"A": w["A"]}, cost_in_r=0.0, regime=ctx)
    labels = CLF.labels(idx)
    up_boxes = sum(1 for i in range(1, w["A"].n) if labels[i] is Regime.UP)
    assert longs.size == shorts.size == up_boxes


def test_position_boxed_respects_the_gate_too():
    idx, w = world()
    ctx = RegimeContext(CLF, "IDX", idx)
    s = spec(horizon=Horizon.MULTI_DAY, exits=(Exit(ExitKind.TIME, (("bars", 3),)),))
    trades = position_boxed.run(to_engine(s), {"A": w["A"]}, seed=0, regime=ctx)
    labels = CLF.labels(idx)
    assert trades and all(labels[t.day] is Regime.UP for t in trades)


def test_the_forward_runner_refuses_a_gated_spec_without_its_classifier(tmp_path):
    from occams.forward.runner import open_window
    from occams.forward.window import ForwardWindow
    from occams.telegram import DryRunTransport
    from occams.venues.proposal import ProposalVenue
    with pytest.raises(GateRefusal):
        open_window(to_engine(spec()), ForwardWindow(3, 30), venue=ProposalVenue(DryRunTransport()),
                    register=Register(tmp_path / "r.jsonl"), operations=Operations(tmp_path / "o.jsonl"),
                    min_size=Money(1.0, "XXX"), hypothesis_id="H", now=datetime(2026, 9, 11, tzinfo=UTC))


def test_measure_question_reads_the_frozen_classifier_from_the_register(tmp_path):
    from occams.hypothesis import Confirmation
    from occams.ledger.alpha_budget import AlphaBudget
    from occams.measurement import Floor
    from occams.proposers.base import Draft, Sweep
    from occams.question import from_draft, measure_question, register_question
    from occams.hypothesis import Gates
    raw = copy.deepcopy(FIXTURE)
    raw["capital"]["currency"] = "USD"
    raw["alpha"]["axes"]["regime"] = {"budget": 0.5, "mechanism_test_alpha": 0.1, "implementation_test_alpha": 0.05}
    c = parse(raw, Path("fixture"))
    arch = BarArchive(tmp_path / "a")
    for n, sd in (("SPY", 1), ("A", 2), ("B", 3)):
        arch.put(random_walk(n, days=1500, seed=sd, sigma_daily=0.015), ActionSeries(), source_id="synthetic")
    reg = Register(tmp_path / "r.jsonl")
    clf = freeze(arch, c, register=reg, level=ClusterLevel.INDEX, index_name="SPY", seed=1, config_sha="x")
    gated = spec(gate=RegimeGate(clf.frozen_hash, Regime.UP, "SPY"))
    d = Draft(proposer="t", axis=InformationAxis.REGIME, mechanism="m", if_true="t", if_false="f", falsifier="x",
              floor=Floor(0.5, 20), sweep=Sweep((("stop", (2.0, 3.0)),)), sigma_r=1.2, sigma_provenance="fixture",
              power=0.8, gates=Gates(2, 0.3, 0.5, 50.0), alternative_ev_net_r=0.9)
    b = AlphaBudget(c, reg, config_sha="x")
    q = from_draft(d, id="Q-G", template=gated, budget=b, available_n=2000)
    q = register_question(q, confirmation=Confirmation("author", True), budget=b, register=reg, declared=None)
    q, m = measure_question(q, cfg=c, archive=arch, register=reg, seed=2, null_draws=200)
    assert m.winner.n > 0 and m.winner.n < 3 * 750  # gated: fewer boxes than the measurement partition holds
    # a stale gate — a classifier hash the Register does not hold — is refused before anything runs
    stale = from_draft(d, id="Q-S", template=spec(gate=RegimeGate("deadbeef" * 8, Regime.UP, "SPY")), budget=b, available_n=2000)
    stale = register_question(stale, confirmation=Confirmation("author", True), budget=b, register=reg, declared=None)
    with pytest.raises(GateRefusal, match="D2"):
        measure_question(stale, cfg=c, archive=arch, register=reg, seed=2, null_draws=50)


def test_m4_11_a_label_known_between_two_venues_closes_refuses_the_earlier_venues_bar_in_the_engine():
    """ADR-0020, D10: the label meets the bar through the instant gate, not the
    ordinal. An LSE name and a NYSE name share ordinals; the index's label for
    day d is known at 18:00 UTC on day d — between the LSE close (16:30 UTC)
    and the NYSE close (21:00 UTC). By ordinal both bars would take it; by
    instant the LSE bar closed before it was known and is refused, in the
    engine, not only in the gate's unit test."""
    from dataclasses import replace
    from datetime import date, time

    from occams.data.instants import session_close

    idx, w = world()
    start = date(2020, 1, 1).toordinal()

    def closes(venue):
        return tuple(session_close(date.fromordinal(start + d), venue).isoformat() for d in idx.day)
    lon = replace(w["A"], name="LON", close_at=closes("LSE"))
    nyc = replace(w["A"], name="NYC", close_at=closes("NYSE"))
    # the index bar the label for day d reads is bar d-1; stamp its close at 18:00 UTC on day d — an ordinal that lies about when the label was known
    late = replace(idx, close_at=tuple(datetime.combine(date.fromordinal(start + d + 1), time(18, 0), tzinfo=UTC).isoformat() for d in idx.day))
    ctx, plain = RegimeContext(CLF, "IDX", late), RegimeContext(CLF, "IDX", idx)
    boxes = [f for f in range(60, 400) if admits(spec().regime, plain, w["A"], f)]      # the up-regime boxes, by ordinal
    assert boxes
    assert all(admits(spec().regime, ctx, nyc, f) for f in boxes)                         # NYSE closes after the label is known
    assert not any(admits(spec().regime, ctx, lon, f) for f in boxes)                     # LSE closed before it
    assert len(day_boxed.run(to_engine(spec()), {"LON": lon}, seed=0, regime=ctx)) == 0   # refused in the engine
    assert len(day_boxed.run(to_engine(spec()), {"NYC": nyc}, seed=0, regime=ctx)) > 0
    # instants that agree with the ordinals admit both; bars without instants are admitted by ordinal as before
    honest = RegimeContext(CLF, "IDX", replace(idx, close_at=closes("NYSE")))
    assert len(day_boxed.run(to_engine(spec()), {"LON": lon}, seed=0, regime=honest)) > 0
    assert [admits(spec().regime, ctx, w["A"], f) for f in boxes] == [True] * len(boxes)
