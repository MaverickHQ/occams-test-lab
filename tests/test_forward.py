"""M9.4 replay identically twice · M9.4b real orders at minimum size via
the proposal path, paper refused · M9.5 three outcomes · M9.6 the wording ·
M9.7 the card from the decision · M9.8 acknowledgement, never a veto."""

from __future__ import annotations

import dataclasses
import inspect
from datetime import datetime, timedelta, UTC

import pytest

from occams.cards import Acknowledgement, Decision, render
from occams.config import InformationAxis
from occams.data.bars import random_walk
from occams.forward.replay import ReplaySource, fill_at_open
from occams.forward.runner import ForwardRefused, open_window, resolve, step
from occams.forward.window import PASS_STATEMENT, ForwardWindow, Outcome, evaluate
from occams.guards import Refused
from occams.register import Money, Operations, Register
from occams.spec import (Capability, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType, Side, Sizing, Stop,
                         StopKind, StrategySpec, UniverseRule, to_engine)
from occams.telegram import DryRunTransport, TelegramTransport, TransportError
from occams.venues.paper import PaperVenue
from occams.venues.proposal import ProposalVenue

CAPS = frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS})
T0 = datetime(2026, 9, 11, 21, 0, tzinfo=UTC)
MIN = Money(1.0, "XXX")  # fixture: minimum size in a fictional account currency, never a recommendation


def spec():
    return StrategySpec(entries=(Entry(EntryKind.CLOSE_ABOVE_MA, Side.LONG, (("lookback", 5),)),),
                        exits=(Exit(ExitKind.TIME, (("bars", 1),)),), stop=Stop(StopKind.PERCENT, 2.0),
                        sizing=Sizing(), order_type=OrderType.MARKET, horizon=Horizon.INTRADAY,
                        universe=UniverseRule((("venue", "NYSE"),)), required_capabilities=CAPS,
                        axis=InformationAxis.PRICE_DAILY)


def world(days=40):
    return {n: random_walk(n, days=days, seed=s, sigma_daily=0.015, drift_daily=0.002) for n, s in (("A", 1), ("B", 2))}


def run_replay(tmp_path, tag, *, window=ForwardWindow(3, 30), days=40, defects_bound=1e9):
    reg, ops = Register(tmp_path / f"r{tag}.jsonl"), Operations(tmp_path / f"o{tag}.jsonl")
    venue = ProposalVenue(DryRunTransport())
    run = open_window(to_engine(spec()), window, venue=venue, register=reg, operations=ops, min_size=MIN,
                      hypothesis_id="H-F", now=T0, slippage_bound=defects_bound)
    src = ReplaySource(world(days), fill_at_open)
    for i, (day, known) in enumerate(src.feed()):
        at = T0 + timedelta(days=i)
        step(run, known, day, at=at, acknowledge=lambda d, b, at=at: src.acknowledge(d, b, at.isoformat()))
    return run, reg, ops, venue


# ---- M9.4 ---------------------------------------------------------------------------

def test_a_replay_is_identical_twice(tmp_path):
    a, ra, oa, va = run_replay(tmp_path, "a")
    b, rb, ob, vb = run_replay(tmp_path, "b")
    assert [f[0] for f in a.fills] == [f[0] for f in b.fills] and a.trades == b.trades > 0
    assert va.transport.sent == vb.transport.sent
    strip = lambda rows: [{k: v for k, v in r.items() if k != "at"} for r in rows]  # noqa: E731
    assert strip(oa.records()) == strip(ob.records())


def test_the_feed_never_shows_a_future_bar():
    src = ReplaySource(world(10), fill_at_open)
    for day, known in src.feed():
        assert all(max(b.day) == day for b in known.values())


# ---- M9.4b ---------------------------------------------------------------------------

def test_a_forward_window_on_the_paper_venue_is_refused_by_name(tmp_path):
    reg, ops = Register(tmp_path / "r.jsonl"), Operations(tmp_path / "o.jsonl")
    with pytest.raises(Refused, match="cannot evidence cost or obtainability"):
        open_window(to_engine(spec()), ForwardWindow(3, 30), venue=PaperVenue(), register=reg, operations=ops,
                    min_size=MIN, hypothesis_id="H", now=T0)
    assert reg.records()[-1]["type"] == "RefusalRecorded"


def test_a_fill_becomes_a_live_exposure_at_minimum_size_in_operations_not_the_register(tmp_path):
    run, reg, ops, venue = run_replay(tmp_path, "x")
    exp = ops.live_exposures(run.compiled.spec_hash)
    assert exp and exp[0]["risk"] == {"amount": 1.0, "currency": "XXX"}
    assert "XXX" not in reg.path.read_text() and "amount" not in reg.path.read_text()


def test_minimum_size_must_be_positive_and_comes_from_config(tmp_path):
    with pytest.raises(ForwardRefused, match="minimum size"):
        open_window(to_engine(spec()), ForwardWindow(3, 30), venue=ProposalVenue(DryRunTransport()),
                    register=Register(tmp_path / "r.jsonl"), operations=Operations(tmp_path / "o.jsonl"),
                    min_size=Money(0.0, "XXX"), hypothesis_id="H", now=T0)


# ---- M9.5 / M9.6 ------------------------------------------------------------------------

def test_three_outcomes():
    w = ForwardWindow(5, 30)
    assert evaluate(w, trades=5, days_elapsed=10, defects=()).outcome is Outcome.PASS
    assert evaluate(w, trades=5, days_elapsed=10, defects=("obtainability: x",)).outcome is Outcome.REJECTED
    assert evaluate(w, trades=2, days_elapsed=30, defects=()).outcome is Outcome.FREQUENCY_FAILURE
    assert evaluate(w, trades=2, days_elapsed=10, defects=()) is None  # not yet due
    with pytest.raises(ValueError, match="vacuous"):
        ForwardWindow(0, 30)


def test_pass_rejected_and_frequency_failure_through_the_runner(tmp_path):
    run, reg, *_ = run_replay(tmp_path, "p", window=ForwardWindow(3, 60))
    res = resolve(run, now=T0 + timedelta(days=45))
    assert res.outcome is Outcome.PASS and res.statement == PASS_STATEMENT
    run2, *_ = run_replay(tmp_path, "r", window=ForwardWindow(3, 60), defects_bound=-1.0)  # every fill 'adverse'
    assert resolve(run2, now=T0 + timedelta(days=45)).outcome is Outcome.REJECTED
    run3, *_ = run_replay(tmp_path, "f", window=ForwardWindow(10_000, 30))
    assert resolve(run3, now=T0 + timedelta(days=45)).outcome is Outcome.FREQUENCY_FAILURE


def test_the_window_is_evaluated_once(tmp_path):
    run, *_ = run_replay(tmp_path, "o", window=ForwardWindow(3, 60))
    resolve(run, now=T0 + timedelta(days=45))
    with pytest.raises(ForwardRefused, match="once"):
        resolve(run, now=T0 + timedelta(days=46))
    with pytest.raises(ForwardRefused, match="evaluated"):
        step(run, world(5), 1, at=T0, acknowledge=lambda d, b: None)


def test_the_register_says_no_defect_found_not_edge_confirmed(tmp_path):
    run, reg, *_ = run_replay(tmp_path, "w", window=ForwardWindow(3, 60))
    resolve(run, now=T0 + timedelta(days=45))
    rec = [r for r in reg.records() if r["type"] == "ForwardWindowResolved"][-1]
    assert rec["statement"] == "no implementation, cost or obtainability defect was found; the edge is not confirmed"
    assert "not confirmed" in rec["statement"] and rec["statement"].count("confirmed") == 1
    assert render(run.fills[0][0]).endswith("it does not change the decision.")


# ---- M9.7 / M9.8 ------------------------------------------------------------------------

def test_the_card_is_the_decision_by_construction(tmp_path):
    run, reg, ops, venue = run_replay(tmp_path, "c")
    d = run.fills[0][0]
    card = venue.transport.sent[0]
    assert d.card_id in card and d.spec_hash[:12] in card and d.instrument in card
    assert f"{d.stop_level:.4f}" in card and f"{d.quantity:g}" in card and ("BUY" if d.side is Side.LONG else "SELL") in card
    assert inspect.signature(render).parameters.keys() == {"d"}  # nothing but the decision goes in


def test_an_acknowledgement_is_never_a_veto_and_logs_the_trade(tmp_path):
    fields = {f.name for f in dataclasses.fields(Acknowledgement)}
    assert fields == {"card_id", "by", "fill_price", "acknowledged_at"}  # no decision field to alter
    venue = ProposalVenue(DryRunTransport())
    d = Decision("h" * 64, "A", Side.LONG, "market", None, 98.0, 2.0, 0.5, T0.isoformat(), 3)
    venue.propose(d)
    back = venue.acknowledge(Acknowledgement(d.card_id, "author", 100.2, T0.isoformat()))
    assert back == d and back is d
    run, reg, ops, _ = run_replay(tmp_path, "l")
    assert [r["type"] for r in ops.records()].count("ForwardFill") == run.trades


def test_the_live_transport_has_no_token_and_no_default():
    with pytest.raises(TransportError, match="TELEGRAM_BOT_TOKEN"):
        TelegramTransport(chat_id="0").send("x")
