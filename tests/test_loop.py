"""M8.6 — the registered queue runs unattended (ADR-0035): never registers,
never touches the reserve, stops when the falsifier fires."""

from __future__ import annotations

import copy
import inspect
from pathlib import Path


from occams import loop as loop_mod
from occams.config import parse
from occams.hypothesis import Confirmation
from occams.ledger.alpha_budget import AlphaBudget
from occams.loop import run
from occams.measurement import Floor
from occams.proposers.base import Sweep
from occams.question import QuestionQueue, from_draft, register_question
from occams.register import Register
from tests.test_config import FIXTURE
from tests.test_question import draft, edge_template, reverting_world, template, world_archive
from tests.test_whatif import AFFORDABLE_AXES

HUMAN = Confirmation("author", True)


def cfg(falsifier_count=1):
    raw = copy.deepcopy(FIXTURE)
    raw["capital"]["currency"] = "USD"
    raw["alpha"]["axes"] = copy.deepcopy(AFFORDABLE_AXES)
    raw["alpha"]["axes"]["regime"]["budget"] = 0.6      # three two-cell questions at 0.1 per cell
    raw["alpha"]["axes"]["price_daily"]["budget"] = 0.15
    raw["lab"] = {"falsifier_count": falsifier_count, "falsifier_outcome": "null", "overlap_threshold": 0.9}
    return parse(raw, Path("fixture"))


def queued(tmp_path, c, ids, *, drift, edge: bool = False):
    """``edge``: the reverting world and the down-run template (ADR-0043) — a drift alone no longer supports a verdict."""
    reg = Register(tmp_path / "r.jsonl")
    budget = AlphaBudget(c, reg, config_sha="fixture")
    arch = reverting_world(tmp_path) if edge else world_archive(tmp_path, drift=drift)
    queue = QuestionQueue(tmp_path / "q.jsonl")
    for i, hid in enumerate(ids):
        # two cells per question: a single cell has no neighbourhood and the plateau check refuses it
        q = from_draft(draft(sweep=Sweep((("stop", (2.0 + i, 2.5 + i)),)), floor=Floor(0.15, 20)), id=hid,
                       template=edge_template() if edge else template(), budget=budget, available_n=900)
        q = register_question(q, confirmation=HUMAN, budget=budget, register=reg, declared=None)
        queue.enqueue(q)
    return reg, arch, queue


def test_two_registered_questions_resolve_unattended(tmp_path):
    c = cfg(falsifier_count=10)
    reg, arch, queue = queued(tmp_path, c, ["Q-1", "Q-2"], drift=0.0, edge=True)
    res = run(c, register=reg, archive=arch, queue=queue, seed=5, null_draws=300, path_draws=50)
    assert [o for _, o in res.resolved] == ["supported", "supported"] and not res.lab_closed
    again = run(c, register=reg, archive=arch, queue=queue, seed=5, null_draws=300, path_draws=50)
    assert again.resolved == () and again.refused == ()  # nothing left to do; nothing re-run


def test_the_loop_never_registers_and_never_touches_the_reserve():
    src = inspect.getsource(loop_mod)
    assert "register_question(" not in src and "transfer_from_reserve" not in src and "Confirmation" not in src
    assert "AlphaBudget" not in src  # it has no accountant handle at all


def test_the_falsifier_stops_the_loop_and_is_recorded(tmp_path):
    c = cfg(falsifier_count=2)
    reg, arch, queue = queued(tmp_path, c, ["Q-1", "Q-2", "Q-3"], drift=0.0)  # driftless: nulls
    res = run(c, register=reg, archive=arch, queue=queue, seed=6, null_draws=300, path_draws=50)
    assert [o for _, o in res.resolved] == ["null", "null"] and res.lab_closed
    types = [r["type"] for r in reg.records()]
    assert types.count("LabClosed") == 1 and types.count("HypothesisResolved") == 2  # Q-3 never ran
    assert run(c, register=reg, archive=arch, queue=queue, seed=6).lab_closed  # closed stays closed


def test_a_refused_measurement_is_logged_and_the_loop_advances(tmp_path):
    c = cfg(falsifier_count=10)
    reg, _, queue = queued(tmp_path, c, ["Q-1"], drift=0.0)
    from occams.data.archive import BarArchive
    res = run(c, register=reg, archive=BarArchive(tmp_path / "empty"), queue=queue, seed=1, null_draws=10)
    assert res.refused and "no bars" in res.refused[0][1] and res.resolved == ()


def test_nothing_registers_after_the_lab_closed(tmp_path):
    """ADR-0033: terminal. The refusal is the Register's, by name, and is
    itself recorded; a capability question is refused too."""
    import pytest

    from occams.guards import Refused
    from occams.hypothesis import Confirmation, Gates, Hypothesis, PowerPlan, Tier, register
    from occams.measurement import Floor
    from occams.register import LabClosed, Register
    from occams.config import InformationAxis
    reg = Register(tmp_path / "r.jsonl")
    reg.append(LabClosed(3, "null", ("Q-1", "Q-2", "Q-3")))
    h = Hypothesis(id="Q-4", tier=Tier.MECHANISM, axis=InformationAxis.PRICE_DAILY, mechanism="m", if_true="t", if_false="f",
                   falsifier="x", floor=Floor(0.15, 50), power_plan=PowerPlan(1.2, 0.05, 0.8, 1000), gates=Gates(4, 0.1, 0.5),
                   search_space_size=1, capability=True)
    with pytest.raises(Refused, match="the lab is closed"):
        register(h, confirmation=Confirmation("apparatus", human=False), parent=None, register=reg)
    assert reg.records()[-1]["type"] == "RefusalRecorded" and "Q-1, Q-2, Q-3" in reg.records()[-1]["reason"]


# ---- M12.6: depth after the verdict, and a seed that is declared, never defaulted ---------------

def test_the_loop_refuses_to_run_without_a_declared_seed(tmp_path, capsys):
    c = cfg(falsifier_count=10)
    reg, arch, queue = queued(tmp_path, c, ["Q-1"], drift=0.0, edge=True)
    cfg_path = tmp_path / "occams.toml"
    from tests.test_console import _toml
    from tests.test_config import FIXTURE
    raw = copy.deepcopy(FIXTURE)
    raw["capital"]["currency"] = "USD"
    raw["alpha"]["axes"] = copy.deepcopy(AFFORDABLE_AXES)
    raw["alpha"]["axes"]["regime"]["budget"] = 0.6
    raw["alpha"]["axes"]["price_daily"]["budget"] = 0.15
    raw["lab"] = {"falsifier_count": 10, "falsifier_outcome": "null", "overlap_threshold": 0.9}
    cfg_path.write_text(_toml(raw), encoding="utf-8")
    args = [str(reg.path), str(tmp_path / "archive"), str(queue.path), "--config", str(cfg_path)]
    assert loop_mod.main(args) == 2 and "declared --seed" in capsys.readouterr().out
    assert loop_mod.main([*args, "--seed"]) == 2
    assert not [r for r in reg.records() if r["type"] == "HypothesisResolved"]   # nothing ran


def test_a_verdict_is_followed_by_the_winners_era_decomposition_with_its_missed_entries(tmp_path):
    c = cfg(falsifier_count=10)
    reg, arch, queue = queued(tmp_path, c, ["Q-1"], drift=0.0, edge=True)
    run(c, register=reg, archive=arch, queue=queue, seed=5, null_draws=300, path_draws=50)
    recs = reg.records()
    (v,) = [r for r in recs if r["type"] == "HypothesisResolved"]
    (e,) = [r for r in recs if r["type"] == "EraDecomposition"]
    assert recs.index(e) > recs.index(v) and e["hypothesis_id"] == "Q-1" and e["spec_hash"] == v["spec_hash"] and e["seed"] == 5
    (m,) = [r for r in recs if r["type"] == "HypothesisMeasured"]
    assert len(e["eras"]) == 3 and sum(x["n"] for x in e["eras"]) == m["n"] and len(e["leave_one_era_out"]) == 3
    assert e["eras"][0]["bounds"][0] < e["eras"][1]["bounds"][0] < e["eras"][2]["bounds"][0]
    assert e["missed"] == 0 and e["missed_by_name"] == {} and e["partition"] == "measurement"
    assert not [r for r in recs if r["type"] == "Shrinkage"]   # not from a survey: nothing to shrink from


def test_the_loop_stamps_its_engine_sha_before_its_first_append(tmp_path, monkeypatch):
    """M14.3: the core's ``engine_sha()`` reads ``git status`` at call time, and the loop appends to a tracked Register
    before it compiles a cell — so every record of a run must carry the sha the loop took at its start, not one that
    its own writes dirtied; after the run the stamp is cleared and the compiler reads the tree again."""
    import occams.core.archive as core_archive
    from occams.spec.compile import current_engine_sha

    calls = []

    def sha_now():
        calls.append(1)
        return "abc123" if len(calls) == 1 else "abc123-dirty"

    monkeypatch.setattr(core_archive, "engine_sha", sha_now)
    c = cfg(falsifier_count=10)
    reg, arch, queue = queued(tmp_path, c, ["Q-1"], drift=0.0, edge=True)
    res = run(c, register=reg, archive=arch, queue=queue, seed=5, null_draws=300, path_draws=50)
    assert [o for _, o in res.resolved] == ["supported"]
    stamped = [r["engine_sha"] for r in reg.records() if "engine_sha" in r]
    assert stamped and set(stamped) == {"abc123"}, stamped         # every record of the run: the tree as the loop found it
    assert len(calls) == 1                                          # the loop read the tree exactly once, at its start
    assert current_engine_sha() == "abc123-dirty" and len(calls) == 2   # the stamp is cleared; the compiler reads the tree again
