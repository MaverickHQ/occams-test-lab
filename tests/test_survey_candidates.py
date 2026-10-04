"""M12.5 — from a recorded survey to registration, still a human act:
candidates one per family, generated Drafts with no standing, and
``question register --from-survey`` through the accountant, stamped
with the cells screened (N6)."""

from __future__ import annotations

import pytest
import copy
import json

import numpy as np
from pathlib import Path

from occams.config import InformationAxis, load
from occams.data.archive import BarArchive
from occams.data.bars import Bars
from occams.engine.day_boxed import NO_ACTIONS
from occams.data.partitions import Partitions, freeze_calendar
from occams.hypothesis import Tier
from occams.ledger.alpha_budget import AlphaBudget
from occams.proposers.regime import ClusterLevel, freeze
from occams.question import Question, QuestionQueue, main as question_main, measure_question
from occams.register import Register
from occams.survey.candidates import (candidates, default_id_prefix, draft_document, engine_note, family_template, gate_ready,
                                      grid_sentence, main as candidates_main, survey_record)
from occams.survey.grid import load as load_grid
from occams.survey.run import run_survey
from occams.universe import main as universe_main
from occams.whatif import config_sha
from tests.test_calendar import LO, latest
from tests.test_config import FIXTURE
from tests.test_console import MONEY, _toml
from tests.test_survey_run import SMALL
from tests.test_whatif import AFFORDABLE_AXES


def affordable_config(tmp_path):
    d = copy.deepcopy(FIXTURE)
    d["capital"].update(MONEY)
    d["alpha"]["axes"] = copy.deepcopy(AFFORDABLE_AXES)   # a 4-cell question costs 0.4; the fixture's 0.5 rate could afford none
    d["alpha"]["axes"]["price_daily"]["budget"] = 0.45     # both axes afford one such question …
    d["alpha"]["reserve"] = 0.05                           # … and the budgets plus the reserve still make the total (S8)
    d["lab"]["overlap_threshold"] = 0.9
    p = tmp_path / "occams.toml"
    p.write_text(_toml(d), encoding="utf-8")
    return load(p), p


def reverting_bars(name: str, *, first: int, days: int, seed: int) -> Bars:
    """A synthetic name with a reversal to find: after two lower closes the
    next day is up. Everything else is a driftless walk, so always-long has
    nothing and the down-run family has a margin — the fixture a survey
    candidate needs, with no claim about any market."""
    rng = np.random.default_rng(seed)
    o, h, lo, c = [], [], [], []
    close = 100.0
    for _ in range(days):
        z, u = rng.standard_normal(), abs(rng.standard_normal())
        r = 0.010 + 0.004 * z if len(c) >= 2 and c[-1] < c[-2] < (c[-3] if len(c) >= 3 else c[-2] + 1) else 0.012 * z
        op = close
        close = close * float(np.exp(r))
        o.append(op)
        c.append(close)
        h.append(max(op, close) * (1 + 0.02 * u))   # ranges wide enough for a 2 % stop to bite
        lo.append(min(op, close) * (1 - 0.02 * u))
    return Bars(name, tuple(o), tuple(h), tuple(lo), tuple(c), tuple(1e6 for _ in o), tuple(first + i for i in range(days)))


def reverting_archive(root) -> BarArchive:
    a = BarArchive(root)
    for i, n in enumerate(("AAA", "BBB", "CCC")):
        a.put(reverting_bars(n, first=LO, days=2400, seed=70 + i), NO_ACTIONS, source_id="synthetic")
    return a


def survey(tmp_path):
    a = reverting_archive(tmp_path / "archive")
    cfg, cfg_path = affordable_config(tmp_path)
    reg_path = tmp_path / "p2.jsonl"
    assert universe_main(["declare", "--register", str(reg_path), "--name", "etfs", "--members", "AAA,BBB,CCC", "--rule", "fixture",
                          "--bias", "none", "--chosen-on", "2026-09-12"]) == 0
    reg = Register(reg_path)
    freeze_calendar(reg, latest(a), split=Partitions.from_config(cfg), config_sha="c", reason="fixture", universe="etfs")
    freeze(a, cfg, register=reg, level=ClusterLevel.INDEX, index_name="AAA", seed=1, config_sha="c", universe="etfs", names=("AAA",))
    grid_path = tmp_path / "grid-t.toml"
    grid_path.write_text(SMALL)
    grid = load_grid(grid_path, register=reg, plateau_cells=4)
    out = tmp_path / "out"
    run_survey(grid, archive=a, register=reg, cfg=cfg, out=out, seed=7, workers=1, log=lambda *_: None)
    return a, cfg, cfg_path, reg, reg_path, grid, grid_path, out


@pytest.mark.slow
def test_candidates_are_gate_ready_cells_one_per_family_priced_by_the_accountant_and_drafted(tmp_path, capsys):
    a, cfg, cfg_path, reg, reg_path, grid, grid_path, out = survey(tmp_path)
    index = json.loads((out / "survey.json").read_text())
    assert survey_record(reg, index)["seq"] == 3 and "engine" in engine_note(index, out)
    budget = AlphaBudget(cfg, reg, config_sha=config_sha(cfg))
    cands = candidates(index, grid, budget=budget)
    assert cands, "the fixture survey has at least one gate-ready cell"
    assert all(gate_ready(c["row"])[0] for c in cands)
    assert len({c["family"].describe() for c in cands}) == len(cands)                       # one per family
    ranks = [(["held", "positive", "margin", "none", "refused"].index(c["tier"]), -c["row"]["margin_net"]) for c in cands]
    assert ranks == sorted(ranks)                                                             # best first
    assert all(c["alpha"] == budget.spend_for(InformationAxis(c["row"]["axis"]), Tier.MECHANISM, c["sweep"]) for c in cands)
    not_ready = [r for r in index["cells"] if not gate_ready(r)[0]]
    assert not_ready and all(gate_ready(r)[1] for r in not_ready)                             # every exclusion has its reason
    # the command lists them, prices them, writes a Draft each, and registers nothing
    drafts = tmp_path / "drafts"
    assert candidates_main([str(grid_path), "--out", str(out), "--register", str(reg_path), "--config", str(cfg_path),
                            "--top", "2", "--drafts", str(drafts)]) == 0
    text = capsys.readouterr().out
    assert "Nothing here is a verdict" in text and "nothing registered, nothing spent" in text and "[ 1]" in text and "[ 3]" not in text
    written = {q.stem for q in drafts.glob("grid-t-seed7/*.md")}
    assert written == {cands[0]["cell"], cands[1]["cell"]}
    body = (drafts / "grid-t-seed7" / f"{cands[0]['cell']}.md").read_text()
    assert "no standing" in body and "not a verdict" in body and cands[0]["row"]["hypothesis"] in body and "--floor-ev FLOOR" in body
    assert all(m not in body for m in ("987654", "1234.5", "4321"))                         # no money value (R9)
    assert sum(1 for r in reg.records() if r["type"] == "HypothesisRegistered") == 0


@pytest.mark.slow
def test_a_survey_the_register_does_not_hold_is_refused_everywhere(tmp_path, capsys):
    a, cfg, cfg_path, reg, reg_path, grid, grid_path, out = survey(tmp_path)
    other = tmp_path / "other.jsonl"
    assert universe_main(["declare", "--register", str(other), "--name", "etfs", "--members", "AAA,BBB,CCC", "--rule", "fixture",
                          "--bias", "none", "--chosen-on", "2026-09-12"]) == 0
    assert candidates_main([str(grid_path), "--out", str(out), "--register", str(other), "--no-drafts"]) == 1
    assert "not a SurveyRecorded record" in capsys.readouterr().out
    cid = candidates(json.loads((out / "survey.json").read_text()), grid)[0]["cell"]
    assert question_main(["prepare", "--from-survey", str(out), "--grid", str(grid_path), "--ids", cid, "--archive", str(tmp_path / "archive"),
                          "--register", str(other), "--config", str(cfg_path), "--floor-ev", "0.1", "--floor-frequency", "1"]) == 1
    assert "not a SurveyRecorded record" in capsys.readouterr().out


@pytest.mark.slow
def test_register_from_survey_is_the_authors_yes_naming_the_ids_and_stamps_the_cells_screened(tmp_path, capsys):
    a, cfg, cfg_path, reg, reg_path, grid, grid_path, out = survey(tmp_path)
    index = json.loads((out / "survey.json").read_text())
    budget = AlphaBudget(cfg, reg, config_sha=config_sha(cfg))
    cands = candidates(index, grid, budget=budget)
    top = cands[0]
    assert budget.check(InformationAxis(top["row"]["axis"]), Tier.MECHANISM, top["sweep"]) is None
    # the survey's own lowest affordable floor is computed at the chosen cell's dispersion; the plan is made at the family's
    # widest cell's since ADR-0050, where 0.1 R is underpowered and 0.15 R is not
    cid, floor = top["cell"], "0.15"
    assert top["row"]["lowest_affordable_floor"]["4"] == "0.1"
    common = ["--from-survey", str(out), "--grid", str(grid_path), "--archive", str(tmp_path / "archive"), "--register", str(reg_path),
              "--config", str(cfg_path), "--floor-ev", floor, "--floor-frequency", "1", "--seed", "3", "--id-prefix", "Q2-", "--plateau-slack-se", "50"]
    # prepare shows every number and spends nothing
    assert question_main(["prepare", *common, "--ids", cid]) == 0
    text = capsys.readouterr().out
    assert "POWERED" in text and "the R4.9 distinction" in text and "nothing registered, nothing spent" in text and "screened" in text
    # the trades promised are the sweep's thinnest cell's, not the hold-1 template's signals (Q3-001, 2026-09-20)
    assert "the sweep's thinnest cell on the definition partition" in text and "available_n is the lesser" in text
    thin = min(r["trades"] for r in index["cells"] if r["cell"] == cid or (r["universe"] == top["row"]["universe"]
               and r["regime"] == top["row"]["regime"] and r["kind"] == top["row"]["kind"] and r["params"] == top["row"]["params"]
               and bool(r["target"]) == bool(top["row"]["target"]) and r["stop_kind"] == top["row"]["stop_kind"]))
    assert f"— {thin} trades" in text or f"— {thin:,} trades" in text
    assert sum(1 for r in reg.records() if r["type"] == "HypothesisRegistered") == 0
    # two ids of one family are one question: refused by name before any spend
    sibling = next(r["cell"] for r in index["cells"] if r["cell"] != cid and r["universe"] == top["row"]["universe"]
                   and r["regime"] == top["row"]["regime"] and r["kind"] == top["row"]["kind"] and r["params"] == top["row"]["params"]
                   and bool(r["target"]) == bool(top["row"]["target"]))
    assert question_main(["register", *common, "--ids", f"{cid},{sibling}", "--by", "author", "--yes"]) == 1
    assert "one family" in capsys.readouterr().out
    # a cell that is not gate-ready is refused with its reason
    weak = next(r["cell"] for r in index["cells"] if not gate_ready(r)[0])
    assert question_main(["register", *common, "--ids", weak, "--by", "author", "--yes"]) == 1
    assert "not gate-ready" in capsys.readouterr().out
    # without --yes nothing registers
    assert question_main(["register", *common, "--ids", cid, "--by", "author"]) == 2
    assert "human act" in capsys.readouterr().out
    assert sum(1 for r in reg.records() if r["type"] == "HypothesisRegistered") == 0
    # the author's --yes: registered through the accountant, stamped, queued
    assert question_main(["register", *common, "--ids", cid, "--by", "author", "--yes"]) == 0
    text = capsys.readouterr().out
    assert "REGISTERED Q2-001 by author" in text and "stamped (N6)" in text
    recs = [r for r in reg.records() if r["type"] == "HypothesisRegistered"]
    assert len(recs) == 1 and recs[0]["hypothesis_id"] == "Q2-001" and recs[0]["screened_cells"] == index["cell_count"] == 32
    assert recs[0]["survey_cell"] == cid and recs[0]["survey_results_sha"] == index["results_sha"] and recs[0]["universe"] == "etfs"
    assert recs[0]["mechanism"] == top["row"]["hypothesis"] and recs[0]["alpha_spent"] > 0 and recs[0]["search_space_size"] == top["sweep"]
    queue = QuestionQueue(tmp_path / "p2-queue.jsonl")
    (q,) = queue.questions()
    assert q.id == "Q2-001" and q.hypothesis.survey["cell"] == cid and q.hypothesis.survey["screened_cells"] == 32
    assert q.hypothesis.survey["definition"]["margin_net"] == top["row"]["margin_net"] and q.sweep.size == top["sweep"]
    assert Question.from_json(q.to_json()) == q                                                # the stamp survives the queue
    # the loop would measure it on the universe's own calendar and members (M12.5 → M12.6)
    q2, m = measure_question(q, cfg=cfg, archive=a, register=reg, seed=3, null_draws=50)
    assert m.partition == "measurement" and m.winner.n > 0 and set(m.winner.groups) <= {"AAA", "BBB", "CCC"}
    # M12.6: the loop resolves it and records the winner's eras with its missed entries, and the shrinkage from screening
    from occams.loop import run as loop_run

    res = loop_run(cfg, register=reg, archive=a, queue=queue, seed=3, null_draws=100, path_draws=20)
    assert [h for h, _o in res.resolved] == ["Q2-001"]
    recs = reg.records()
    (v,) = [r for r in recs if r["type"] == "HypothesisResolved"]
    (e,) = [r for r in recs if r["type"] == "EraDecomposition"]
    (sh,) = [r for r in recs if r["type"] == "Shrinkage"]
    assert sh["hypothesis_id"] == "Q2-001" and sh["survey_cell"] == cid and sh["screened_cells"] == 32
    assert sh["definition_ev_net"] == top["row"]["ev_net"] and sh["definition_margin_net"] == top["row"]["margin_net"]
    assert sh["measured_ev_net"] == v["ev_net_r"] and sh["ev_shrinkage"] == sh["measured_ev_net"] - sh["definition_ev_net"]
    assert sh["measured_margin_net"] == sh["measured_ev_net"] - sh["measured_baseline_ev_net"] and sh["measured_trades"] > 0
    assert e["hypothesis_id"] == "Q2-001" and sum(x["n"] for x in e["eras"]) == sh["measured_trades"] and isinstance(e["missed"], int)
    # the console shows the screen beside the verdict, the eras and the shrinkage table
    from occams.console import build

    page, facts = build(reg_path, controls="none", generated="g", repo_sha="x")
    (fd,) = facts.findings
    assert fd.shrinkage and fd.depth and "Shrinkage from screening" in page and "Eras on the measurement partition" in page
    assert "From the survey" in page and cid in page and "Missed entries" in page


@pytest.mark.slow
def test_the_fifth_check_is_shown_on_the_definition_partition_before_alpha_moves(tmp_path, capsys):
    """ADR-0043 on the survey's candidates: always-long re-run at each cell's
    geometry and gate, the guard's Monte Carlo, the margin per era; a table
    is written; nothing is registered."""
    import importlib.util
    import sys

    a, cfg, cfg_path, reg, reg_path, grid, grid_path, out = survey(tmp_path)
    table = tmp_path / "docs" / "readiness.md"
    assert candidates_main([str(grid_path), "--out", str(out), "--register", str(reg_path), "--config", str(cfg_path), "--no-drafts",
                            "--fifth-check", "--archive", str(tmp_path / "archive"), "--draws", "600", "--readiness-out", str(table)]) == 0
    text = capsys.readouterr().out
    assert "beats-always-long on the definition partition (ADR-0043)" in text and "PASS" in text and "margin by era" in text
    assert "pass the fifth check on the definition partition" in text and "readiness table written" in text
    body = table.read_text(encoding="utf-8")
    assert body.startswith("# Readiness under the fifth check — grid-t seed 7") and "| Fifth check |" in body and "**pass**" in body
    # an earlier programme's Shrinkage records are cited as priors, read-only (ADR-0046)
    from tests.test_programme_page import second_programme
    second_programme(tmp_path / "earlier.jsonl")
    earlier_before = (tmp_path / "earlier.jsonl").read_text()
    assert candidates_main([str(grid_path), "--out", str(out), "--register", str(reg_path), "--config", str(cfg_path), "--no-drafts",
                            "--fifth-check", "--archive", str(tmp_path / "archive"), "--draws", "600", "--readiness-out", str(table),
                            "--priors-register", str(tmp_path / "earlier.jsonl")]) == 0
    capsys.readouterr()
    body = table.read_text(encoding="utf-8")
    assert "`Q2-001` (earlier.jsonl) from cell `cell0123456789ab`: definition margin +0.428 → measured margin +0.260" in body
    assert (tmp_path / "earlier.jsonl").read_text() == earlier_before
    assert "nothing here is a verdict" in body and "the definition partition only" in body
    spec = importlib.util.spec_from_file_location("_prepublish", Path(__file__).resolve().parent.parent / "tools" / "prepublish.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    assert mod.check_page(body, name="readiness") == []
    assert sum(1 for r in reg.records() if r["type"] == "HypothesisRegistered") == 0
    # the flag needs the bars and the corrected alpha
    assert candidates_main([str(grid_path), "--out", str(out), "--register", str(reg_path), "--no-drafts", "--fifth-check"]) == 2


@pytest.mark.slow
def test_a_family_with_targets_declares_the_capability_its_target_cells_need(tmp_path):
    """Found 2026-09-18 preparing grid-001's candidates: a target family's
    template derived its capabilities from the no-target first hold, so its
    target cells refused to compile at measurement. Every cell compiles."""
    from occams.question import apply_cell
    from occams.spec.compile import to_engine
    from occams.spec.spec import Capability

    a, cfg, cfg_path, reg, reg_path, grid, grid_path, out = survey(tmp_path)
    index = json.loads((out / "survey.json").read_text())
    with_targets = [f for f in grid.families if f.targets]
    plain = [f for f in grid.families if not f.targets]
    assert with_targets and plain
    for fam in with_targets + plain:
        template = family_template(fam, index["classifier_hash"])
        assert (Capability.RESTING_ORDERS in template.required_capabilities) == bool(fam.targets)
        from itertools import product
        axes = fam.sweep.as_dict()
        for values in product(*axes.values()):
            to_engine(apply_cell(template, dict(zip(axes, values, strict=True))))   # every cell of the sweep compiles from the family's template


@pytest.mark.slow
def test_the_claim_registered_is_the_grids_sentence_and_the_cell_files_wording_is_stamped_beside_it(tmp_path, capsys):
    """A survey's cell file records the proposer's sentence on the day it ran (it is under the results hash); the R4.9
    distinction a question is registered with is the grid's sentence now, and when the two differ the recorded one is
    stamped beside it — never silently replaced, never registered as the claim."""
    a, cfg, cfg_path, reg, reg_path, grid, grid_path, out = survey(tmp_path)
    index = json.loads((out / "survey.json").read_text())
    budget = AlphaBudget(cfg, reg, config_sha=config_sha(cfg))
    top = candidates(index, grid, budget=budget)[0]
    cid, fam, row = top["cell"], top["family"], top["row"]
    assert top["hypothesis"] == grid_sentence(fam, row) == row["hypothesis"]          # freshly run: the two agree
    assert "cell file recorded" not in draft_document(top, index, survey_record(reg, index), out=out, grid_path=grid_path)
    # the cell file's wording drifts from the grid's (a proposer template corrected after the survey ran)
    stale = row["hypothesis"] + " with no regime gate"
    for r in index["cells"]:
        if r["cell"] == cid:
            r["hypothesis"] = stale
    (out / "survey.json").write_text(json.dumps(index))
    index = json.loads((out / "survey.json").read_text())
    top = candidates(index, grid, budget=budget)[0]
    assert top["cell"] == cid and top["hypothesis"] == grid_sentence(fam, row) and top["survey_hypothesis"] == stale
    doc = draft_document(top, index, survey_record(reg, index), out=out, grid_path=grid_path)
    assert grid_sentence(fam, row) in doc and "cell file recorded" in doc and stale in doc
    common = ["--from-survey", str(out), "--grid", str(grid_path), "--archive", str(tmp_path / "archive"), "--register", str(reg_path),
              "--config", str(cfg_path), "--floor-ev", "0.15", "--floor-frequency", "1", "--seed", "3", "--plateau-slack-se", "50"]
    # a Register whose name does not say which programme it is gets no prefix by default: refused, not numbered as another's
    assert question_main(["prepare", *common, "--ids", cid]) == 1
    assert "does not name its programme" in capsys.readouterr().out
    common += ["--id-prefix", "Q2-", "--plateau-slack-se", "50"]
    assert question_main(["prepare", *common, "--ids", cid]) == 0
    text = capsys.readouterr().out
    assert f"the R4.9 distinction): {grid_sentence(fam, row)} — on etfs" in text and "cell file recorded it as" in text and stale in text
    assert question_main(["register", *common, "--ids", cid, "--by", "author", "--yes"]) == 0
    (rec,) = [r for r in reg.records() if r["type"] == "HypothesisRegistered"]
    assert rec["mechanism"] == grid_sentence(fam, row) and "no regime gate" not in rec["mechanism"]
    (q,) = QuestionQueue(tmp_path / "p2-queue.jsonl").questions()
    assert q.hypothesis.distinction == f"{grid_sentence(fam, row)} — on etfs" and q.hypothesis.survey["survey_hypothesis"] == stale


def test_question_ids_are_numbered_by_the_register_the_programme_owns():
    """Programme 1's Register is register.jsonl and its questions are Q-NNN; programme N's is programme-N.jsonl and its
    questions QN-NNN. A Register named otherwise implies no prefix: the command refuses rather than number a third
    programme's questions as the second's (found on 2026-09-20, when a prepare on programme 3 printed Q2-001)."""
    assert default_id_prefix("register/register.jsonl") == "Q-"
    assert default_id_prefix("register/programme-2.jsonl") == "Q2-"
    assert default_id_prefix(Path("/x/register/programme-3.jsonl")) == "Q3-"
    assert default_id_prefix("register/programme-12.jsonl") == "Q12-"
    assert default_id_prefix("register/p2.jsonl") is None and default_id_prefix("register/programme-2-queue.jsonl") is None
