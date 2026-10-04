"""M16.18 (ADR-0047; the review's T02, T22, T23) — the diagnostic re-score.

What the corrected rules would have said of a question is written beside the record, never
in its place: in its own hash-chained store, with one record kind, after the question's
recorded numbers are recreated exactly from its stamped source. A re-score is not a verdict.
It moves no falsifier, spends no alpha, and no closed Register gains a line."""

from __future__ import annotations

import json
from dataclasses import fields
from pathlib import Path

import pytest

from occams import rescore
from occams.config import load
from occams.ledger.alpha_budget import AlphaBudget
from occams.question import QuestionQueue, measure_question, resolve_question
from occams.register import FORBIDDEN_IN_REGISTER, Diagnostics, Register, Rescored
from occams.register.heads import head_of
from occams.whatif import config_sha
from tests.test_question import _registered
from tests.test_reproduce import config_on_disk

ROOT = Path(__file__).resolve().parents[1]


def test_rescored_is_the_diagnostics_stores_one_record_and_no_register_takes_it(tmp_path):
    """ADR-0047 §3: one record kind, in its own store. A programme Register refuses it — a stopped Register gains no
    record, and an annotation is a record — and the diagnostics store refuses a verdict."""
    from occams.register import HypothesisResolved, RefusalRecorded

    assert Rescored.__diagnostic_record__ and not getattr(Rescored, "__register_record__", False)
    assert not {f.name for f in fields(Rescored)} & FORBIDDEN_IN_REGISTER                      # S7: no money, by declaration
    rec = Rescored(hypothesis_id="Q-1", register="r.jsonl", annotates_seq=3, annotates_sha="a" * 64, recorded={"outcome": "supported"},
                   reproduced=True, reproduction={"source": "c" * 40}, rescored=True, rules=rescore.RULES, engine_sha="c" * 40,
                   engine_code_sha="e" * 16, seed=1, null_draws=100, winner={}, at_measurement={"passed": True}, checks=(),
                   refused_by=(), reading="would be supported")
    with pytest.raises(TypeError, match="not a Register record"):
        Register(tmp_path / "r.jsonl").append(rec)
    d = Diagnostics(tmp_path / "d.jsonl")
    d.append(rec)
    for other in (RefusalRecorded("a->b", "x", {}, None, None),
                  HypothesisResolved("Q-1", "supported", 0.2, 100.0, "s", "e", 1, "measurement", ())):
        with pytest.raises(TypeError, match="not a Diagnostics record"):
            d.append(other)
    assert d.verify() == 1 and d.records()[0]["type"] == "Rescored"


@pytest.fixture
def programme(tmp_path):
    """A small programme of one supported verdict, measured and resolved by this code, with its queue and its config."""
    reg = Register(tmp_path / "r.jsonl")
    cfg_path = config_on_disk(tmp_path)
    c = load(cfg_path)
    c, reg, budget, arch, q = _registered((c, reg, AlphaBudget(c, reg, config_sha=config_sha(c))), tmp_path, drift=0.0, edge=True)
    queue = QuestionQueue(tmp_path / "q.jsonl")
    queue.enqueue(q)
    q, m = measure_question(q, cfg=c, archive=arch, register=reg, seed=3, null_draws=300)
    q, v, _ = resolve_question(q, m, register=reg, archive=arch, seed=3, path_draws=50)
    assert v.outcome == "supported"
    return rescore.Programme(reg.path, queue.path, cfg_path), tmp_path / "archive", v, m


def _as_recorded(v, m):
    """A reproduction that recreates the stamped numbers: what a stamped source returns when the record is honest."""
    return lambda **kw: {"spec_hash": v.spec_hash, "ev_net_r": v.ev_net_r, "n": m.winner.n, "refusals": list(v.refusals)}


def test_a_rescore_reproduces_first_and_then_records_every_number(programme, tmp_path):
    prog, archive, v, m = programme
    out = Diagnostics(tmp_path / "diagnostics.jsonl")
    (rec,) = rescore.run([prog], archive=archive, out=out, null_draws=300, measure_at_source=_as_recorded(v, m))
    assert rec["hypothesis_id"] == "Q-1" and rec["register"] == "r.jsonl" and rec["reproduced"] is True and rec["rescored"] is True
    chain = Register(prog.register).chain()
    resolved = next(line for line in chain if line["payload"]["type"] == "HypothesisResolved")
    assert rec["annotates_seq"] == resolved["seq"] and rec["annotates_sha"] == resolved["sha"]       # by the chain, not by name
    assert rec["recorded"]["outcome"] == "supported" and rec["recorded"]["ev_net_r"] == v.ev_net_r and rec["recorded"]["n"] == m.winner.n
    assert rec["rules"] == list(rescore.RULES) and "ADR-0048" in rec["rules"] and "ADR-0050" in rec["rules"]
    assert rec["seed"] == 3 and rec["null_draws"] == 300 and len(rec["engine_code_sha"]) == 16
    names = [c["check"] for c in rec["checks"]]
    assert names == ["plateau", "beats_null", "clears_floor", "leave_one_out", "beats_always_long"]
    by = {c["check"]: c for c in rec["checks"]}
    assert all(c["evidence"] for c in rec["checks"]) and all(isinstance(c["passed"], bool) for c in rec["checks"])
    assert by["beats_null"]["evidence"]["p_null"] > 0 and "p_cluster" in by["beats_null"]["evidence"]
    assert by["clears_floor"]["evidence"]["rule"] == "lower confidence bound" and "lcb_ev_net_r" in by["clears_floor"]["evidence"]
    assert "selection" in by["beats_always_long"]["evidence"] and by["beats_always_long"]["evidence"]["long_share"] == 1.0
    assert rec["reading"] in ("would be supported", "would be null", "would be refused at measurement")
    assert rec["refused_by"] == [c["check"] for c in rec["checks"] if c["judged"] and not c["passed"]] or rec["reading"] == "would be refused at measurement"
    assert rec["winner"]["n"] > 0 and "is_the_recorded_winner" in rec["winner"] and rec["at_measurement"]["passed"] in (True, False)
    assert out.verify() == 1


def test_a_question_that_cannot_be_recreated_is_recorded_and_not_rescored(programme, tmp_path):
    """ADR-0047 §4: reproduce first. A source that returns other numbers, or none, is a record with its reason."""
    prog, archive, v, m = programme
    out = Diagnostics(tmp_path / "diagnostics.jsonl")
    moved = lambda **kw: {"spec_hash": v.spec_hash, "ev_net_r": v.ev_net_r + 0.01, "n": m.winner.n, "refusals": []}   # noqa: E731
    (rec,) = rescore.run([prog], archive=archive, out=out, null_draws=300, measure_at_source=moved)
    assert rec["reproduced"] is False and rec["rescored"] is False and rec["reading"] == "not re-scored"
    assert "ev_net_r" in rec["reproduction"]["differs"] and rec["checks"] == [] and rec["winner"] == {}

    def absent(**kw):
        raise rescore.sources.SourceMissing("no snapshot of abc at archive/source/abc.tar.gz")

    out2 = Diagnostics(tmp_path / "d2.jsonl")
    (rec,) = rescore.run([prog], archive=archive, out=out2, null_draws=300, measure_at_source=absent)
    assert rec["reproduced"] is False and "no snapshot" in rec["reproduction"]["reason"] and rec["reading"] == "not re-scored"


def test_a_rescore_is_not_a_verdict(programme, tmp_path):
    """The programme's Register is the bytes it was; its falsifier stands where it stood; no alpha moved; and a second
    run adds nothing — a question is re-scored once."""
    from occams import falsifier

    prog, archive, v, m = programme
    cfg = load(prog.config)
    before = Path(prog.register).read_bytes()
    head = head_of(Path(prog.register))
    reg = Register(prog.register)
    budget = AlphaBudget(cfg, reg, config_sha=config_sha(cfg))
    standing, balances = falsifier.standing(cfg, reg), {ax: budget.remaining(ax) for ax in cfg.alpha.axes}
    out = Diagnostics(tmp_path / "diagnostics.jsonl")
    rescore.run([prog], archive=archive, out=out, null_draws=300, measure_at_source=_as_recorded(v, m))
    assert Path(prog.register).read_bytes() == before and head_of(Path(prog.register)) == head
    reg = Register(prog.register)
    budget = AlphaBudget(cfg, reg, config_sha=config_sha(cfg))
    assert falsifier.standing(cfg, reg) == standing and {ax: budget.remaining(ax) for ax in cfg.alpha.axes} == balances
    assert rescore.run([prog], archive=archive, out=out, null_draws=300, measure_at_source=_as_recorded(v, m)) == []
    assert out.verify() == 1


def test_a_question_refused_at_measurement_stamps_no_source(tmp_path):
    """Q3-001 was refused at REGISTERED -> MEASURED: its refusal names a count and no engine. There is no stamped source
    to recreate it from, and it says so."""
    reg = Register(tmp_path / "r.jsonl")
    cfg_path = config_on_disk(tmp_path)
    c = load(cfg_path)
    c, reg, budget, arch, q = _registered((c, reg, AlphaBudget(c, reg, config_sha=config_sha(c))), tmp_path, drift=0.0, edge=True)
    queue = QuestionQueue(tmp_path / "q.jsonl")
    queue.enqueue(q)
    reg.append(reg.RefusalRecorded("REGISTERED->MEASURED", "the winning cell holds fewer trades than the power plan requires",
                                   {"required_n": 1068, "n": 863}, None, "Q-1"))
    out = Diagnostics(tmp_path / "diagnostics.jsonl")
    (rec,) = rescore.run([rescore.Programme(reg.path, queue.path, cfg_path)], archive=tmp_path / "archive", out=out, null_draws=300,
                         measure_at_source=lambda **kw: pytest.fail("there is nothing to reproduce at"))
    assert rec["reproduced"] is False and rec["rescored"] is False and rec["recorded"]["outcome"] == "refused at measurement"
    assert "stamps no engine" in rec["reproduction"]["reason"] and rec["recorded"]["evidence"] == {"required_n": 1068, "n": 863}


def test_a_rescore_refuses_dirty_code(programme, tmp_path, monkeypatch):
    from occams import identity

    prog, archive, v, m = programme
    monkeypatch.setattr(identity, "dirty_paths", lambda root=identity.ROOT: ("occams/rescore.py",))
    with pytest.raises(identity.EngineNotClean, match="a re-score"):
        rescore.run([prog], archive=archive, out=Diagnostics(tmp_path / "d.jsonl"), null_draws=300, measure_at_source=_as_recorded(v, m))
    assert not (tmp_path / "d.jsonl").exists() or Diagnostics(tmp_path / "d.jsonl").verify() == 0


def test_every_number_in_a_record_is_a_number():
    """Evidence comes from guards that may hold a not-a-number; the chain holds none."""
    assert rescore.clean({"a": float("nan"), "b": [float("inf"), 1.0], "c": {"d": (2, float("-inf"))}}) == {"a": None, "b": [None, 1.0], "c": {"d": [2, None]}}
    assert json.loads(json.dumps(rescore.clean({"x": float("nan")}))) == {"x": None}


def test_old_code_meets_the_register_and_the_queue_as_they_were(programme, tmp_path):
    """The first run of the re-score handed the code of 2026-09-11 a queue that held a question registered a day later,
    with an entry kind that code had never heard of, and recorded two questions as not recreated. A stamped source is
    given the Register up to the question's own measurement and a queue that holds that question alone."""
    from occams import reproduce
    from occams.question import QuestionQueue, QuestionQueued
    from occams.register.store import Store

    prog, archive, v, m = programme
    queue = QuestionQueue(prog.queue)
    mine = queue.records()[0]["question_json"]
    queue.append(QuestionQueued("Q-2", mine.replace('"Q-1"', '"Q-2"').replace("down_run", "a_kind_from_the_future")))
    dest = tmp_path / "scratch"
    dest.mkdir()
    reg, q = reproduce.as_it_was("Q-1", prog.register, prog.queue, dest)
    types = [json.loads(ln)["payload"]["type"] for ln in reg.read_text().splitlines()]
    assert "HypothesisMeasured" not in types and "HypothesisResolved" not in types and "HypothesisRegistered" in types
    assert Store(reg).verify() == len(types) and Path(prog.register).read_text().startswith(reg.read_text())     # a prefix, and a chain
    (only,) = QuestionQueue(q).records()
    assert only["hypothesis_id"] == "Q-1" and "a_kind_from_the_future" not in only["question_json"]
    assert only["question_json"] == json.loads(Path(prog.queue).read_text().splitlines()[0])["payload"]["question_json"]   # its own words
    with pytest.raises(RuntimeError, match="not in the queue"):
        reproduce.as_it_was("Q-9", prog.register, prog.queue, dest)


def test_a_failure_is_recorded_in_one_line_with_no_path_of_this_machine():
    from occams import reproduce

    stderr = "\n".join(["Traceback (most recent call last):", '  File "/Users/someone/work/occams/spec/spec.py", line 237, in <genexpr>',
                        "    entries=tuple(...)", "ValueError: 'down_run' is not a valid EntryKind", ""])
    assert reproduce.last_words(stderr) == "ValueError: 'down_run' is not a valid EntryKind"
    assert "/Users/" not in reproduce.last_words("FileNotFoundError: no bars at /Users/someone/private/archive/bars/SPY.json")
    assert reproduce.last_words("") == "the child said nothing"
