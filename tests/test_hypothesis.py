"""M2.1 — DRAFT -> REGISTERED -> MEASURED -> RESOLVED, two tiers (D3). An
implementation Hypothesis without a resolved mechanism parent raises."""

from __future__ import annotations

import dataclasses

import pytest

from occams.config import InformationAxis
from occams.guards import Refused
from occams.hypothesis import (Confirmation, Gates, Hypothesis, HypothesisState, PowerPlan, Tier,
                               Verdict, measure, register, resolve)
from occams.measurement import Floor
from occams.register import Register
from occams.engine import synthetic
from occams.ledger.alpha_budget import AlphaBudget
from occams.config import parse
from tests.test_config import FIXTURE
from pathlib import Path as _P


def budget(reg):
    return AlphaBudget(parse(__import__("copy").deepcopy(FIXTURE), _P("fixture")), reg, config_sha="fixture")

HUMAN = Confirmation(by="author", human=True)
APPARATUS = Confirmation(by="apparatus", human=False)


def draft(**kw) -> Hypothesis:
    # the regime axis: fixture budget 0.5 at a mechanism rate of 0.5 per cell, so one
    # single-cell question spends the whole axis — absurd on purpose, and it makes
    # the accountant's refusals show up in these tests
    base = dict(id="H-1", tier=Tier.MECHANISM, axis=InformationAxis.REGIME,
                mechanism="m", if_true="t", if_false="f", falsifier="x",
                floor=Floor(0.15, 50), power_plan=PowerPlan(1.2, 0.05, 0.8, 1000, alternative_ev_net_r=0.45),
                gates=Gates(4, 0.10, 0.5, 50.0), search_space_size=1)
    base.update(kw)
    return Hypothesis(**base)


def measurement(spec_hash="s", seed=1, effect=0.2):
    # a single-cell sweep, matching draft()'s declared search_space_size of 1
    return synthetic.measure(spec_hash=spec_hash, seed=seed, axes={"a": [1], "b": [1]},
                             groups=list("ABCDE"), years=10, trades_per_group_year=20,
                             sigma_r=1.2, cost_in_r=0.05, effect=synthetic.flat(effect), null_draws=4000)


@pytest.fixture
def reg(tmp_path):
    return Register(tmp_path / "register.jsonl")


def test_registration_spends_rate_times_search_space(reg):
    b = budget(reg)  # fixture: price_daily mechanism rate 0.5 per cell, budget 0.25
    h = register(draft(), confirmation=HUMAN, parent=None, register=reg, budget=b)
    assert h.state is HypothesisState.REGISTERED and h.alpha_spent == pytest.approx(0.5 * 1)
    assert [r["type"] for r in reg.records()][-2:] == ["AlphaSpent", "HypothesisRegistered"]


def test_spending_alpha_needs_a_human(reg):
    with pytest.raises(Refused) as e:
        register(draft(), confirmation=APPARATUS, parent=None, register=reg, budget=budget(reg))
    assert "human" in str(e.value)
    assert reg.records()[-1]["type"] == "RefusalRecorded"  # recorded, never discarded


def test_a_capability_question_registers_at_alpha_zero_without_the_accountant(reg):
    h = register(draft(capability=True), confirmation=APPARATUS, parent=None, register=reg)
    assert h.alpha_spent == 0.0


def test_a_market_question_without_the_accountant_is_refused(reg):
    with pytest.raises(Refused, match="accountant"):
        register(draft(), confirmation=HUMAN, parent=None, register=reg)


def test_implementation_without_resolved_mechanism_parent_raises(reg):
    child = draft(id="H-2", tier=Tier.IMPLEMENTATION, parent_id="H-1")
    with pytest.raises(Refused) as e:
        register(child, confirmation=HUMAN, parent=None, register=reg, budget=budget(reg))
    assert "resolved mechanism parent" in str(e.value)
    unresolved = register(draft(), confirmation=HUMAN, parent=None, register=reg, budget=budget(reg))
    with pytest.raises(Refused):
        register(child, confirmation=HUMAN, parent=unresolved, register=reg, budget=budget(reg))


def test_implementation_with_resolved_supporting_parent_is_accepted(reg):
    parent = register(draft(), confirmation=HUMAN, parent=None, register=reg, budget=budget(reg))
    m = measurement(effect=0.4)  # comfortably above the 0.15R floor after the 0.05 cost
    parent = measure(parent, m, register=reg)
    v = Verdict("supported", m.winner.ev, m.winner.n / m.years, m.spec_hash, m.engine_sha, m.seed, m.partition, ())
    parent = resolve(parent, v, register=reg)
    assert parent.state is HypothesisState.RESOLVED and parent.spec_hash == m.spec_hash
    assert parent.consumed is not None and parent.consumed.names == frozenset("ABCDE")  # M6.6
    b = budget(reg)  # the parent drained the axis; a child needs a recorded transfer from reserve (R4.7)
    b.transfer_from_reserve(InformationAxis.REGIME, 0.25, decision="test: fund the implementation child")
    child = register(draft(id="H-2", tier=Tier.IMPLEMENTATION, parent_id="H-1", search_space_size=1),
                     confirmation=HUMAN, parent=parent, register=reg, budget=b)
    assert child.state is HypothesisState.REGISTERED and child.alpha_spent == pytest.approx(0.25)


def test_implementation_on_a_null_parent_is_refused(reg):
    parent = register(draft(), confirmation=HUMAN, parent=None, register=reg, budget=budget(reg))
    m = measurement(effect=-0.3)
    parent = measure(parent, m, register=reg)
    v = Verdict("null", m.winner.ev, m.winner.n / m.years, m.spec_hash, m.engine_sha, m.seed, m.partition, ("floor",))
    parent = resolve(parent, v, register=reg)
    with pytest.raises(Refused) as e:
        register(draft(id="H-2", tier=Tier.IMPLEMENTATION, parent_id="H-1"),
                 confirmation=HUMAN, parent=parent, register=reg, budget=budget(reg))
    assert "null" in str(e.value)


def test_underpowered_is_refused_at_measure_not_discovered_after(reg):
    h = register(draft(power_plan=PowerPlan(1.2, 0.05, 0.8, available_n=100, alternative_ev_net_r=0.30)),
                 confirmation=HUMAN, parent=None, register=reg, budget=budget(reg))
    assert h.required_n > 100
    with pytest.raises(Refused) as e:
        measure(h, measurement(), register=reg)
    assert "underpowered" in str(e.value)


def test_required_n_is_the_m0_15_formula():
    h = draft(search_space_size=4, power_plan=PowerPlan(1.2, 0.05, 0.8, 1000))
    assert h.required_n == 714  # docs/M0-ANSWERS.md §M0.15: 0.15R, sigma 1.2, k=4, 80%


def test_verdict_must_name_the_measured_spec(reg):
    h = register(draft(), confirmation=HUMAN, parent=None, register=reg, budget=budget(reg))
    m = measurement()
    h = measure(h, m, register=reg)
    with pytest.raises(Refused):
        resolve(h, Verdict("supported", 0.3, 100, "other", m.engine_sha, 1, "measurement", ()), register=reg)


def test_a_verdict_cannot_contradict_the_declared_floor(reg):
    h = register(draft(), confirmation=HUMAN, parent=None, register=reg, budget=budget(reg))
    m = measurement(effect=-0.3)
    h = measure(h, m, register=reg)
    with pytest.raises(Refused) as e:
        resolve(h, Verdict("supported", m.winner.ev, 100, m.spec_hash, m.engine_sha, 1, "measurement", ()), register=reg)
    assert "contradicts" in str(e.value)


def test_instances_are_frozen_and_transitions_return_new_ones(reg):
    d = draft()
    h = register(d, confirmation=HUMAN, parent=None, register=reg, budget=budget(reg))
    assert d.state is HypothesisState.DRAFT and h.state is HypothesisState.REGISTERED
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.state = HypothesisState.RESOLVED  # type: ignore[misc]
