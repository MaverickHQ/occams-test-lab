"""ADR-0043 — the fifth check. A signal that only rides the drift of its
world is refused by name; both real engines supply the always-long
distribution beside the null; a verdict names the checks it was judged
against, and the conclusion reads an older verdict as four."""

from __future__ import annotations

import pytest
from occams.engine import day_boxed, position_boxed
from occams.guards import forward
from occams.question import measure_question, resolve_question
from occams.spec.compile import to_engine
from occams.spec.spec import Horizon
from occams.ledger.alpha_budget import AlphaBudget
from occams.register import Register
from tests.test_question import _registered, cfg, edge_template, reverting_world, template  # noqa: F401


def test_a_signal_that_only_rides_the_drift_is_refused_by_name(tmp_path):
    # the always-long template in a drifting world: beats-null (a coin-flip side) and the floor pass; the fifth refuses
    reg = Register(tmp_path / "r.jsonl")
    c = cfg()
    lab = (c, reg, AlphaBudget(c, reg, config_sha="fixture"))
    c, reg, budget, arch, q = _registered(lab, tmp_path, drift=0.012)
    q, m = measure_question(q, cfg=c, archive=arch, register=reg, seed=3, null_draws=400)
    assert len(m.baseline_ev) == 400
    q, v, deployable = resolve_question(q, m, register=reg, archive=arch, seed=3, path_draws=200)
    assert v.outcome == "null" and deployable is None
    # M16.12: the winner *is* always-long, so its margin is nil, and leave-one-out now refuses a pooled score with nothing to
    # preserve by name — it used to pass it. The fifth check refused then and refuses now; the verdict is null either way.
    assert [r.split(":")[0] for r in v.refusals] == ["leave-one-out", "beats-always-long"] and m.score(m.winner) == 0.0
    assert v.refusals[0] == "leave-one-out: the pooled score is not positive; leave-one-out has nothing to preserve"
    assert v.checks == forward.CHECKS
    rec = [r for r in reg.records() if r["type"] == "HypothesisResolved"][-1]
    assert tuple(rec["checks"]) == forward.CHECKS and rec["refusals"][-1].startswith("beats-always-long: the passive alternative")
    assert rec["surface"] == "margin" and m.surface == "margin"                                  # ADR-0045: the record names its surface
    ev = [r for r in reg.records() if r["type"] == "RefusalRecorded"][-1]["evidence"]
    assert ev["p_baseline"] > ev["alpha_corrected"] and "baseline_mean" in ev


@pytest.mark.slow
def test_both_engines_carry_the_always_long_distribution(tmp_path):
    arch = reverting_world(tmp_path)
    bars = {n: b for n, (b, _) in arch.latest_bars().items()}
    axes = {"stop": [2.0, 3.0]}

    def cell(t, params):
        return t.replace(stop=t.stop.__class__(t.stop.kind, params["stop"]))
    intraday = edge_template()
    m1 = day_boxed.measure(intraday, axes, cell, bars, seed=1, cost_in_r=0.05, null_draws=300)
    assert len(m1.baseline_ev) == 300 and len(m1.null_ev) == 300
    assert sum(m1.baseline_ev) / 300 < m1.winner.ev          # a reverting world: the entry beats being long
    assert m1.surface == "margin" and all(c.baseline_ev is not None and c.baseline_by_group for c in m1.cells)   # ADR-0045
    assert {g for g, _e, _n in m1.winner.baseline_by_group} == {"A", "B", "C"} and m1.winner.margin == max(c.margin for c in m1.cells)
    multi = intraday.replace(horizon=Horizon.MULTI_DAY)
    m2 = position_boxed.measure(multi, axes, cell, bars, seed=1, cost_in_r=0.05, null_draws=300)
    assert len(m2.baseline_ev) == 300 and sum(m2.baseline_ev) / 300 < m2.winner.ev
    assert m2.surface == "margin" and m2.winner.margin == max(c.margin for c in m2.cells)
    # ADR-0045, before alpha moves: the definition surface names the margin winner
    from occams.proposers.base import Sweep
    from occams.proposers.regime import definition_surface
    rows = definition_surface(multi, Sweep((("stop", (2.0, 3.0)),)), bars, ctx=None, seed=1)
    assert [r["margin"] for r in rows] == sorted((r["margin"] for r in rows), reverse=True) and all(r["baseline_ev"] is not None for r in rows)
    assert to_engine(multi).spec_hash != to_engine(intraday).spec_hash


def test_the_conclusion_reads_an_older_verdict_as_four_checks():
    from occams.conclude import CHECKS, FOUR, _checks
    from occams.console.facts import Finding
    old = Finding({"hypothesis_id": "Q-0"}, None, [], None, {"refusals": ["floor: EV per trade in net R is below the declared floor"]},
                  None, [], [])
    ch = _checks(old)
    assert ch["beats-always-long"] == "not evaluated" and ch["floor"].startswith("refused") and ch["beats-null"] == "passed"
    new = Finding({"hypothesis_id": "Q-1"}, None, [], None, {"refusals": [], "checks": list(forward.CHECKS)}, None, [], [])
    assert all(_checks(new)[c] == "passed" for c in CHECKS) and len(FOUR) == 4
