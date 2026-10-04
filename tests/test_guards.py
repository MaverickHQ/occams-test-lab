"""M2.4 — one module per transition; each guard has a test that makes it
refuse for its stated reason."""

from __future__ import annotations

from types import SimpleNamespace


from occams.config import InformationAxis
from occams.guards import (approve, compile, halt, live, measure, register as g_register, resolve,
                           resume, retire, measured)
from occams.hypothesis import Confirmation, Gates, Hypothesis, HypothesisState, PowerPlan, Tier, Verdict
from occams.measurement import Floor
from occams.strategy import Strategy, StrategyState as S
from occams.engine import synthetic


def draft(**kw) -> Hypothesis:
    base = dict(id="H-1", tier=Tier.MECHANISM, axis=InformationAxis.PRICE_DAILY,
                mechanism="m", if_true="t", if_false="f", falsifier="x",
                floor=Floor(0.15, 50), power_plan=PowerPlan(1.2, 0.05, 0.8, 1000, alternative_ev_net_r=0.45),
                gates=Gates(4, 0.10, 0.5, 50.0), search_space_size=9)
    base.update(kw)
    return Hypothesis(**base)


def m(effect=0.2, seed=1, spec_hash="s"):
    return synthetic.measure(spec_hash=spec_hash, seed=seed, axes={"a": [1, 2, 3], "b": [1, 2, 3]},
                             groups=list("ABCDE"), years=10, trades_per_group_year=20,
                             sigma_r=1.2, cost_in_r=0.05, effect=synthetic.flat(effect), null_draws=4000)


HUMAN = Confirmation("author", True)


def test_register_refuses_an_incomplete_draft():
    r = g_register.check(draft(falsifier=" ", capability=True), confirmation=HUMAN, parent=None)
    assert r is not None and "incomplete" in r.reason and r.evidence["missing"] == ["falsifier"]


def test_register_refuses_alpha_spend_without_a_human():
    r = g_register.check(draft(), confirmation=Confirmation("apparatus", False), parent=None, budget=object())
    assert r is not None and "human" in r.reason


def test_register_refuses_a_market_question_without_the_accountant():
    r = g_register.check(draft(), confirmation=HUMAN, parent=None)
    assert r is not None and "accountant" in r.reason


def test_register_refuses_a_mechanism_with_a_parent():
    r = g_register.check(draft(parent_id="H-0", capability=True), confirmation=HUMAN, parent=None)
    assert r is not None and "no parent" in r.reason


def test_register_refuses_cross_axis_parent():
    parent = draft(id="H-0", axis=InformationAxis.REGIME, state=HypothesisState.RESOLVED,
                   verdict=Verdict("supported", 0.2, 100, "s", "e", 1, "measurement", ()))
    r = g_register.check(draft(id="H-1", tier=Tier.IMPLEMENTATION, parent_id="H-0", capability=True),
                         confirmation=HUMAN, parent=parent)
    assert r is not None and "different axis" in r.reason


def test_measure_refuses_underpowered():
    h = draft(power_plan=PowerPlan(1.2, 0.05, 0.8, 10), state=HypothesisState.REGISTERED)
    r = measure.check(h, m())
    assert r is not None and "underpowered" in r.reason and r.evidence["required_n"] > 10


def test_measure_refuses_a_sweep_that_is_not_the_declared_one():
    h = draft(search_space_size=4, state=HypothesisState.REGISTERED)
    r = measure.check(h, m())  # 9 cells ran
    assert r is not None and "not the sweep that was declared" in r.reason


def test_resolve_refuses_a_verdict_for_another_spec():
    h = draft(state=HypothesisState.MEASURED, spec_hash="s")
    r = resolve.check(h, Verdict("supported", 0.3, 100, "other", "e", 1, "measurement", ()))
    assert r is not None and "different spec" in r.reason


def test_compile_refuses_without_a_stop():
    r = compile.check(Strategy.specify({"kind": "x"}), SimpleNamespace())
    assert r is not None and "no stop" in r.reason


def test_measured_refuses_a_measurement_of_another_spec():
    s = Strategy.specify({"stop": 1.0}, hypothesis_id="H-1")
    r = measured.check(s, SimpleNamespace(measurement=m(spec_hash="other")))
    assert r is not None and "different spec" in r.reason


def test_approve_refuses_without_a_resolved_supporting_hypothesis():
    s = Strategy.specify({"stop": 1.0}, state=S.FORWARD) if False else Strategy(identity=(("stop", 1.0),), state=S.FORWARD)
    assert approve.check(s, SimpleNamespace(hypothesis=None)).reason.startswith("approval cites no")
    h = draft(state=HypothesisState.RESOLVED, verdict=Verdict("null", 0.0, 100, s.spec_hash, "e", 1, "measurement", ("floor",)))
    assert "null" in approve.check(s, SimpleNamespace(hypothesis=h)).reason
    h2 = draft(state=HypothesisState.RESOLVED, verdict=Verdict("supported", 0.3, 100, "different", "e", 1, "measurement", ()))
    assert "equal resolved hash" in approve.check(s, SimpleNamespace(hypothesis=h2)).reason
    h3 = draft(state=HypothesisState.RESOLVED, verdict=Verdict("supported", 0.3, 100, s.spec_hash, "e", 1, "measurement", (), cost_basis="bounded"))
    assert approve.check(s, SimpleNamespace(hypothesis=h3)) is None
    h4 = draft(state=HypothesisState.RESOLVED, verdict=Verdict("supported", 0.3, 100, s.spec_hash, "e", 1, "measurement", ()))
    assert "optimistic" in approve.check(s, SimpleNamespace(hypothesis=h4)).reason  # cost basis unknown (M5.2)


def test_live_refuses_without_a_signature_and_refuses_with_one_until_m10():
    s = Strategy(identity=(("stop", 1.0),), state=S.APPROVED)
    assert "signature" in live.check(s, SimpleNamespace()).reason
    assert "not built" in live.check(s, SimpleNamespace(signature=object())).reason


def test_halt_refuses_an_unattributed_halt_and_nothing_else():
    s = Strategy(identity=(("stop", 1.0),), state=S.LIVE)
    assert "name who halted" in halt.check(s, SimpleNamespace(halted_by="")).reason
    assert halt.check(s, SimpleNamespace(halted_by="author")) is None


def test_resume_refuses_until_the_cause_clears_and_a_human_acts():
    s = Strategy(identity=(("stop", 1.0),), state=S.HALTED)
    assert "not cleared" in resume.check(s, SimpleNamespace(cause_cleared=False, resumed_by="author")).reason
    assert "human action" in resume.check(s, SimpleNamespace(cause_cleared=True, resumed_by="")).reason
    assert "not built" in resume.check(s, SimpleNamespace(cause_cleared=True, resumed_by="author")).reason


def test_retire_refuses_without_a_reason():
    s = Strategy(identity=(("stop", 1.0),), state=S.LIVE)
    assert "reason" in retire.check(s, SimpleNamespace(reason="")).reason
    assert retire.check(s, SimpleNamespace(reason="hypothesis resolved null")) is None
