"""M6 — the alpha budget and the search budget."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from occams import config as cfgmod
from occams.config import InformationAxis, parse
from occams.core import stats  # noqa: F401
from occams.guards import Refused
from occams.hypothesis import Confirmation, Gates, Hypothesis, HypothesisState, PowerPlan, Tier, Verdict, register
from occams.ledger import alpha_budget as ab
from occams.ledger.alpha_budget import AlphaBudget, Consumed, SearchBudget, donor_replay, overlap
from occams.measurement import Floor
from occams.register import Register
from tests.test_config import FIXTURE

HUMAN = Confirmation("author", True)
ROOT = Path(__file__).resolve().parent.parent


def cfg():
    return parse(copy.deepcopy(FIXTURE), Path("fixture"))  # regime 0.5 @ 0.5/0.25 ; price_daily 0.25 @ 0.5/0.25 ; reserve 0.25


def hyp(**kw) -> Hypothesis:
    base = dict(id="H-1", tier=Tier.MECHANISM, axis=InformationAxis.REGIME, mechanism="m", if_true="t", if_false="f",
                falsifier="x", floor=Floor(0.15, 50), power_plan=PowerPlan(1.2, 0.5, 0.8, 1000), gates=Gates(4, 0.1, 0.5),
                search_space_size=1)
    base.update(kw)
    return Hypothesis(**base)


@pytest.fixture
def reg(tmp_path):
    return Register(tmp_path / "r.jsonl")


# ---- M6.1 naming ----------------------------------------------------------------

def test_no_identifier_collides_with_a_vendored_name():
    import importlib
    vendored = set()
    for m in ("stats", "estimators", "power", "calibration", "result", "archive", "audit", "experiment", "backfill",
              "privacy", "charset", "execution"):
        mod = importlib.import_module(f"occams.core.{m}")
        vendored |= {n for n in dir(mod) if not n.startswith("_")}
    ours = {n for n in dir(ab) if not n.startswith("_") and getattr(getattr(ab, n), "__module__", "") == ab.__name__}
    assert ours and ours.isdisjoint(vendored), ours & vendored
    assert not hasattr(ab, "alpha") and not hasattr(ab, "ledger")  # D17


# ---- M6.2 / M6.3 ---------------------------------------------------------------------

def test_declared_total_reserve_and_axes_hold_s8_on_load_and_after_a_transfer(reg):
    b = AlphaBudget(cfg(), reg, config_sha="x")
    b.invariant()
    b.transfer_from_reserve(InformationAxis.CROSS_SECTIONAL, 0.1, decision="reopen cross_sectional: data acquired")
    b.invariant()
    assert b.reserve == pytest.approx(0.15) and b.remaining(InformationAxis.CROSS_SECTIONAL) == pytest.approx(0.1)
    with pytest.raises(ValueError, match="decision"):
        b.transfer_from_reserve(InformationAxis.REGIME, 0.01, decision=" ")
    with pytest.raises(ValueError):
        b.transfer_from_reserve(InformationAxis.REGIME, 1.0, decision="too much")


def test_cross_axis_spend_is_impossible_by_construction(reg):
    b = AlphaBudget(cfg(), reg, config_sha="x")
    b.charge("H-1", InformationAxis.REGIME, Tier.MECHANISM, 1)
    assert b.remaining(InformationAxis.REGIME) == pytest.approx(0.0)
    assert b.remaining(InformationAxis.PRICE_DAILY) == pytest.approx(0.25)  # untouched


def test_balances_are_replayed_from_the_register(reg):
    b = AlphaBudget(cfg(), reg, config_sha="x")
    b.charge("H-1", InformationAxis.PRICE_DAILY, Tier.IMPLEMENTATION, 1)  # 0.25 * 1
    again = AlphaBudget(cfg(), reg, config_sha="x")
    assert again.remaining(InformationAxis.PRICE_DAILY) == pytest.approx(0.0)


def test_per_test_rates_are_not_extra_pools(reg):
    b = AlphaBudget(cfg(), reg, config_sha="x")
    b.charge("H-1", InformationAxis.REGIME, Tier.IMPLEMENTATION, 2)  # 0.25 x 2 from the same 0.5
    assert b.remaining(InformationAxis.REGIME) == pytest.approx(0.0)


# ---- M6.4 ------------------------------------------------------------------------------

def test_corrected_spend_is_rate_times_search_space_and_a_proposer_sets_neither(reg):
    b = AlphaBudget(cfg(), reg, config_sha="x")
    assert b.spend_for(InformationAxis.REGIME, Tier.MECHANISM, 1) == pytest.approx(0.5)
    assert b.plan_alpha(InformationAxis.REGIME, Tier.IMPLEMENTATION, 2) == pytest.approx(0.5)
    from occams.proposers.base import Draft
    assert "alpha" not in {f.name for f in __import__("dataclasses").fields(Draft)}
    assert "search_space_size" not in {f.name for f in __import__("dataclasses").fields(Draft)}  # computed from the sweep


def test_one_mechanism_and_one_child_debit_the_same_axis(reg):
    b = AlphaBudget(cfg(), reg, config_sha="cfg-1")
    parent = register(hyp(), confirmation=HUMAN, parent=None, register=reg, budget=b)
    assert parent.alpha_spent == pytest.approx(0.5) and parent.config_sha == "cfg-1"
    assert b.remaining(InformationAxis.REGIME) == pytest.approx(0.0)
    spent = [r for r in reg.records() if r["type"] == "AlphaSpent"]
    assert spent[-1]["config_sha"] == "cfg-1" and spent[-1]["alpha_spent"] == pytest.approx(0.5)


# ---- M6.5 / M6.7 ---------------------------------------------------------------------

def test_exhaustion_refuses_both_tiers_and_new_data_accrues_without_a_decision(reg):
    b = AlphaBudget(cfg(), reg, config_sha="x")
    register(hyp(), confirmation=HUMAN, parent=None, register=reg, budget=b)  # drains regime
    with pytest.raises(Refused, match="AXIS_BUDGET_EXHAUSTED"):
        register(hyp(id="H-2"), confirmation=HUMAN, parent=None, register=reg, budget=b)
    resolved = hyp(id="H-1", state=HypothesisState.RESOLVED,
                   verdict=Verdict("supported", 0.3, 100, "s", "e", 1, "measurement", (), cost_basis="bounded"))
    with pytest.raises(Refused, match="AXIS_BUDGET_EXHAUSTED"):  # the parent check passes; the budget refuses
        register(hyp(id="H-3", tier=Tier.IMPLEMENTATION, parent_id="H-1"), confirmation=HUMAN,
                 parent=resolved, register=reg, budget=b)
    b.accrue(InformationAxis.REGIME, new_observations=500, base_observations=500)  # a year of new bars on a year of base
    assert b.remaining(InformationAxis.REGIME) == pytest.approx(0.5)
    ok = register(hyp(id="H-4"), confirmation=HUMAN, parent=None, register=reg, budget=b)
    assert ok.alpha_spent == pytest.approx(0.5)
    assert any(r["type"] == "AlphaAccrued" for r in reg.records())


def test_a_zero_axis_cannot_run_until_transferred_and_rated(reg):
    b = AlphaBudget(cfg(), reg, config_sha="x")
    with pytest.raises(Refused, match="cannot run"):
        register(hyp(axis=InformationAxis.CROSS_SECTIONAL), confirmation=HUMAN, parent=None, register=reg, budget=b)


# ---- M6.6 / M6.8 ---------------------------------------------------------------------

def test_overlap_is_a_fraction_of_the_new_questions_observations():
    a = Consumed("A", InformationAxis.REGIME, "measurement", 0, 100, frozenset("XYZ"))
    b = Consumed("B", InformationAxis.REGIME, "measurement", 50, 150, frozenset("XY"))
    assert overlap(b, a) == pytest.approx(0.5 * 1.0)   # half the days, all of B's names
    assert overlap(a, b) == pytest.approx(0.5 * 2 / 3)
    assert overlap(Consumed("C", InformationAxis.PRICE_DAILY, "measurement", 0, 100, frozenset("X")), a) == 0.0


def test_a_reworded_duplicate_is_refused_and_a_supersession_is_admitted(reg):
    b = AlphaBudget(cfg(), reg, config_sha="x")
    sb = SearchBudget(reg)
    sb.record(Consumed("H-0", InformationAxis.REGIME, "measurement", 0, 100, frozenset("XYZ")))
    intent = Consumed("H-1", InformationAxis.REGIME, "measurement", 0, 100, frozenset("XYZ"))
    # threshold from config (fixture: 1.0 means only a total overlap refuses); use a tighter one here
    b.cfg = parse({**copy.deepcopy(FIXTURE), "lab": {**FIXTURE["lab"], "overlap_threshold": 0.5}}, Path("f"))
    with pytest.raises(Refused, match="overlap"):
        register(hyp(mechanism="the same question, reworded"), confirmation=HUMAN, parent=None, register=reg,
                 budget=b, declared=intent)
    ok = register(hyp(id="H-2", supersedes="H-0"), confirmation=HUMAN, parent=None, register=reg, budget=b,
                  declared=Consumed("H-2", InformationAxis.REGIME, "measurement", 0, 100, frozenset("XYZ")))
    assert ok.supersedes == "H-0"
    b2 = AlphaBudget(cfg(), reg, config_sha="x")  # the other axis, for the distinction path
    b2.cfg = b.cfg
    b2.transfer_from_reserve(InformationAxis.PRICE_DAILY, 0.25, decision="test: fund a single-cell question")
    ok2 = register(hyp(id="H-3", axis=InformationAxis.PRICE_DAILY, distinction="different exit rule family"),
                   confirmation=HUMAN, parent=None, register=reg, budget=b2,
                   declared=Consumed("H-3", InformationAxis.PRICE_DAILY, "measurement", 0, 100, frozenset("XYZ")))
    assert ok2.distinction


# ---- M6.9 ------------------------------------------------------------------------------

def test_a_capability_question_decrements_nothing(reg):
    b = AlphaBudget(cfg(), reg, config_sha="x")
    h = register(hyp(capability=True), confirmation=Confirmation("apparatus", False), parent=None, register=reg, budget=b)
    assert h.alpha_spent == 0.0
    assert b.remaining(InformationAxis.REGIME) == pytest.approx(0.5) and b.reserve == pytest.approx(0.25)
    assert not any(r["type"] == "AlphaSpent" for r in reg.records())


# ---- M6.10 -----------------------------------------------------------------------------

def test_the_donor_register_replays_to_the_known_answer():
    raw, corrected = donor_replay(ROOT / "tests" / "fixtures" / "donor-register-cache.json")
    assert raw == pytest.approx(0.620) and corrected == pytest.approx(1.700)
    assert corrected > 1.0  # the state this budget forbids: the loader refuses a total above 1


def test_the_loader_refuses_the_donors_corrected_total():
    raw = copy.deepcopy(FIXTURE)
    raw["alpha"]["total"] = 1.7
    with pytest.raises(cfgmod.ConfigRefused):
        parse(raw, Path("fixture"))
