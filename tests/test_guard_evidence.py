"""M16.8 (ADR-0048 §4; the review's F03) — a Monte Carlo p is counted plus one, and a
resolution records what every check saw, passing or failing: a pass leaves its numbers
in the Register, not only its name."""

from __future__ import annotations

from dataclasses import fields, replace
from pathlib import Path

from occams.engine import synthetic
from occams.guards import beats_always_long, beats_null, forward
from occams.hypothesis import PowerPlan
from occams.question import measure_question, resolve_question
from occams.register import FORBIDDEN_IN_REGISTER, Register
from tests.test_forward_refusals import hyp, measure
from tests.test_question import _registered, lab  # noqa: F401 — `lab` is the fixture `_registered` takes

ROOT = Path(__file__).resolve().parents[1]


def test_mc_p_value_is_never_zero():
    """No draw reaching the winner is `at most one in draws + 1`, never zero: the count
    includes the observed value itself (ADR-0048 §4)."""
    from occams.inference import monte_carlo_p

    assert monte_carlo_p((0.0,) * 999, 1.0) == 1 / 1000 and monte_carlo_p((), 1.0) == 1.0
    assert monte_carlo_p((0.0, 2.0, 2.0), 1.0) == 3 / 4
    m = measure(synthetic.flat(0.9))                              # an effect no draw of either distribution reaches
    plan = PowerPlan(1.2, 0.05, 0.8, 1000)
    for guard, key, dist in ((beats_null, "p_null", m.null_ev), (beats_always_long, "p_baseline", m.baseline_ev)):
        refusal, evidence = guard.evaluate(m, plan, 9)
        assert refusal is None and not any(x >= m.winner.ev for x in dist)
        assert evidence[key] == 1 / (len(dist) + 1) > 0


def test_resolution_records_evidence_for_passing_checks(lab, tmp_path):  # noqa: F811
    """Five `GuardEvidence` records before every resolution, in the order of the checks,
    each with the numbers it judged — on a supported verdict, where nothing was refused
    and the Register used to say only that."""
    c, reg, budget, arch, q = _registered(lab, tmp_path, drift=0.0, edge=True)
    q, m = measure_question(q, cfg=c, archive=arch, register=reg, seed=3, null_draws=400)
    q, v, _ = resolve_question(q, m, register=reg, archive=arch, seed=3, path_draws=50)
    assert v.outcome == "supported"
    records = reg.records()
    types = [r["type"] for r in records]
    ev = [r for r in records if r["type"] == "GuardEvidence"]
    assert [r["check"] for r in ev] == list(forward.CHECKS) and all(r["passed"] for r in ev)
    assert max(i for i, t in enumerate(types) if t == "GuardEvidence") < types.index("HypothesisResolved")
    assert all(r["hypothesis_id"] == "Q-1" and r["spec_hash"] == v.spec_hash and r["evidence"] for r in ev)
    by = {r["check"]: r["evidence"] for r in ev}
    assert 0 < by["beats_null"]["p_null"] <= by["beats_null"]["alpha_corrected"] and by["beats_null"]["draws"] == 400
    assert 0 < by["beats_always_long"]["p_baseline"] <= by["beats_always_long"]["alpha_corrected"]
    assert by["clears_floor"]["ev_net_r"] == v.ev_net_r and by["clears_floor"]["floor_ev_net_r"] == 0.15
    assert by["plateau"]["neighbourhood"] >= 2 and "neighbourhood_median" in by["plateau"]
    assert by["leave_one_out"]["groups"] == 3 and "weakest_group" in by["leave_one_out"]


def test_a_refused_check_records_the_same_numbers_its_refusal_does(lab, tmp_path):  # noqa: F811
    c, reg, budget, arch, q = _registered(lab, tmp_path, drift=0.012)       # the drift world: null under the fifth check
    q, m = measure_question(q, cfg=c, archive=arch, register=reg, seed=3, null_draws=300)
    q, v, _ = resolve_question(q, m, register=reg, archive=arch, seed=3, path_draws=50)
    records = reg.records()
    ev = {r["check"]: r for r in records if r["type"] == "GuardEvidence"}
    refused = {r["reason"]: r["evidence"] for r in records if r["type"] == "RefusalRecorded" and r["transition"] == "MEASURED->FORWARD"}
    assert v.outcome == "null" and set(ev) == set(forward.CHECKS) and refused
    assert sum(1 for r in ev.values() if not r["passed"]) == len(refused) == len(v.refusals)
    for reason, numbers in refused.items():
        check = {"beats-null": "beats_null", "beats-always-long": "beats_always_long", "floor": "clears_floor",
                 "plateau": "plateau", "leave-one-out": "leave_one_out"}[reason.split(":")[0]]
        assert not ev[check]["passed"] and ev[check]["evidence"]["reason"] == reason
        assert all(ev[check]["evidence"][k] == x for k, x in numbers.items())


def test_guard_evidence_carries_no_money():
    """S7: the record is publishable by construction, and so is what the guards put in it."""
    from occams.register import GuardEvidence

    assert GuardEvidence.__register_record__ and not {f.name for f in fields(GuardEvidence)} & FORBIDDEN_IN_REGISTER
    m, h = measure(synthetic.flat(0.5)), hyp()
    for name, passed, evidence in forward.evidence(m, h):
        assert name in forward.CHECKS and isinstance(passed, bool)
        assert not {k.lower() for k in evidence} & FORBIDDEN_IN_REGISTER


def test_a_thin_distribution_is_refused_with_its_evidence_and_no_p():
    m = measure(synthetic.flat(0.5))
    refusal, evidence = beats_null.evaluate(replace(m, null_ev=m.null_ev[:100]), PowerPlan(1.2, 0.05, 0.8, 1000), 9)
    assert refusal is not None and "too thin" in refusal.reason and evidence["draws"] == 100 and "p_null" not in evidence


def test_readiness_prints_no_zero_p(tmp_path):
    """The readiness table printed `0.0000 vs 0.01` for a cell no draw reached. It prints
    the plus-one p now, in a form that cannot round to nought — and no committed page says zero."""
    from occams.survey import candidates

    p = candidates.readiness_p((0.0,) * 40_000, 0.5)
    assert p == 1 / 40_001
    row = {"cell": "c" * 16, "universe": "u", "tier": "held", "ev_net": 0.5, "baseline_survey": 0.0, "baseline_now": 0.0,
           "margin_now": 0.5, "p_baseline": p, "alpha_corrected": 0.01, "fifth_check": "pass", "eras_margin": [0.1, 0.1, 0.1],
           "sweep": 15, "alpha": 0.15}
    index = {"grid": "g", "seed": 1, "cell_count": 1, "results_sha": "0" * 64, "engine_shas": {"engine_code_sha": "e"}}
    doc = candidates.readiness_document([row], index, {"seq": 0}, register=Register(tmp_path / "r.jsonl"), draws=40_000, seed=1)
    line = next(x for x in doc.splitlines() if x.startswith("| 1 |"))
    assert "0.0000 vs" not in line and "2.5e-05 vs 0.01" in line
    for page in sorted((ROOT / "docs" / "surveys").glob("*readiness.md")):
        assert "0.0000 vs" not in page.read_text(encoding="utf-8"), page.name
