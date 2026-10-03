"""M12.8 — the conclusion is written from the Register after the programme
stopped, and not before. Three stopping conditions, each a record:
``LabClosed`` (the falsifier, the loop's), ``ProgrammeStopped`` with the
alpha exhausted (verified against the ledger), ``ProgrammeStopped`` by the
author with a reason. After any of them nothing registers, surveys or
measures; the document carries the survey layer and passes the publication
gate's check."""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

from occams.conclude import main as conclude_main
from occams.config import InformationAxis, load
from occams.console.facts import gather
from occams.console.programme import build
from occams.console.render import render
from occams.guards import Refused
from occams.hypothesis import Confirmation, Gates, Hypothesis, PowerPlan, Tier
from occams.hypothesis import register as register_h
from occams.loop import run as loop_run
from occams.measurement import Floor
from occams.question import main as question_main
from occams.stopping import StopRefused, conditions, main as stop_main, stop, stopping_record
from occams.survey.candidates import register_main
from occams.survey.run import SurveyRefused, record_survey
from tests.test_config import FIXTURE
from tests.test_console import MONEY, _toml, fixture_register
from tests.test_programme_page import second_programme
from tests.test_whatif import AFFORDABLE_AXES

ROOT = Path(__file__).resolve().parent.parent


def prepublish():
    spec = importlib.util.spec_from_file_location("_prepublish", ROOT / "tools" / "prepublish.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def config_file(tmp_path: Path, *, rate: float = 0.05) -> Path:
    """regime 0.5 and price_daily 0.25 declared; the fixture programme spent 0.4 on regime."""
    raw = copy.deepcopy(FIXTURE)
    raw["capital"].update(MONEY)
    raw["alpha"]["axes"] = copy.deepcopy(AFFORDABLE_AXES)
    for ax in ("regime", "price_daily"):
        raw["alpha"]["axes"][ax].update(mechanism_test_alpha=rate, implementation_test_alpha=rate / 2)
    raw["lab"] = {"falsifier_count": 3, "falsifier_outcome": "null", "overlap_threshold": 0.9}
    p = tmp_path / "programme.toml"
    p.write_text(_toml(raw), encoding="utf-8")
    return p


def test_the_conclusion_is_refused_until_a_stopping_condition_is_a_record(tmp_path, capsys):
    second_programme(tmp_path / "p2.jsonl")
    cfg = config_file(tmp_path)
    out = tmp_path / "docs" / "conclusion.md"
    assert conclude_main(["--register", str(tmp_path / "p2.jsonl"), "--out", str(out), "--config", str(cfg)]) == 1
    text = capsys.readouterr().out
    assert "REFUSED: no stopping condition is a Register record" in text and not out.exists()
    assert "falsifier: 0 of 3 null mechanism verdicts" in text          # Q2-001 was supported
    assert "alpha on regime: 0.1000 remaining against a smallest charge of 0.2000" in text and "exhausted" in text
    assert "alpha on price_daily: 0.2500 remaining" in text and "affordable" in text and "author's stop: none recorded" in text
    # a plain build names what it cannot show
    assert conclude_main(["--register", str(tmp_path / "p2.jsonl"), "--out", str(out)]) == 1
    text = capsys.readouterr().out
    assert "REFUSED" in text and "pass --config" in text and not out.exists()


def test_an_alpha_stop_is_refused_while_a_question_is_affordable_and_recorded_when_none_is(tmp_path, capsys):
    reg = second_programme(tmp_path / "p2.jsonl")
    cfg = load(config_file(tmp_path))
    c = conditions(cfg, reg)
    assert not c.alpha_exhausted and [r.axis for r in c.room if r.affordable] == ["price_daily"]
    with pytest.raises(StopRefused, match="alpha is not exhausted: price_daily has 0.2500"):
        stop(cfg, reg, kind="alpha", by="author")
    assert stopping_record(reg) is None
    # the command, without --yes, shows the same refusal and appends nothing
    args = ["--register", str(tmp_path / "p2.jsonl"), "--config", str(cfg.path), "--kind", "alpha", "--by", "author"]
    assert stop_main(args) == 1 and "REFUSED: alpha is not exhausted" in capsys.readouterr().out and stopping_record(reg) is None
    # a plateau of six cells costs 0.30 on every runnable axis: nothing is affordable, the stop stands, with the arithmetic in it
    assert stop_main(args + ["--plateau-cells", "6"]) == 0
    text = capsys.readouterr().out
    assert "would append ProgrammeStopped (alpha exhausted, by author)" in text and stopping_record(reg) is None
    assert stop_main(args + ["--plateau-cells", "6", "--yes"]) == 0
    assert "ProgrammeStopped appended (#" in capsys.readouterr().out
    rec = stopping_record(reg)
    assert rec["type"] == "ProgrammeStopped" and rec["kind"] == "alpha_exhausted" and rec["by"] == "author"
    assert rec["alpha_remaining"] == {"regime": 0.1, "price_daily": 0.25} and rec["smallest_charge"] == {"regime": 0.3, "price_daily": 0.3}
    assert rec["verdicts"] == ["Q2-001"] and rec["questions"] == 1 and rec["surveys"] == 1 and "rate × 6 cells" in rec["reason"]
    with pytest.raises(StopRefused, match="already stopped"):
        stop(cfg, reg, kind="author", by="author", reason="again")


def test_an_authors_stop_needs_a_reason_and_a_yes_and_then_nothing_registers_surveys_or_measures(tmp_path, capsys):
    reg = second_programme(tmp_path / "p2.jsonl")
    cfg = load(config_file(tmp_path))
    with pytest.raises(StopRefused, match="names its reason"):
        stop(cfg, reg, kind="author", by="author")
    with pytest.raises(StopRefused, match="names who recorded it"):
        stop(cfg, reg, kind="author", by=" ", reason="enough")
    args = ["--register", str(tmp_path / "p2.jsonl"), "--config", str(cfg.path), "--kind", "author", "--by", "author",
            "--reason", "the second grid is a new programme"]
    n = len(reg.records())
    assert stop_main(args) == 0 and "Nothing appended without --yes" in capsys.readouterr().out and len(reg.records()) == n
    assert stop_main(args + ["--yes"]) == 0 and len(reg.records()) == n + 1
    rec = stopping_record(reg)
    assert rec["kind"] == "author" and rec["reason"] == "the second grid is a new programme" and rec["alpha_remaining"]["regime"] == 0.1
    # registration is refused by the Register, by name, and the refusal is itself recorded
    h = Hypothesis(id="Q2-002", tier=Tier.MECHANISM, axis=InformationAxis.PRICE_DAILY, mechanism="m", if_true="t", if_false="f",
                   falsifier="x", floor=Floor(0.15, 50), power_plan=PowerPlan(1.2, 0.05, 0.8, 1000), gates=Gates(4, 0.1, 0.5),
                   search_space_size=1, capability=True)
    with pytest.raises(Refused, match="the programme is stopped"):
        register_h(h, confirmation=Confirmation("apparatus", human=False), parent=None, register=reg)
    last = reg.records()[-1]
    assert last["type"] == "RefusalRecorded" and "the author stopped it" in last["reason"] and "new programme" in last["reason"]
    # the loop measures nothing more; a survey is not recorded; prepare and register refuse before reading anything
    assert loop_run(cfg, register=reg, archive=None, queue=None, seed=1).lab_closed
    with pytest.raises(SurveyRefused, match="the programme is stopped"):
        record_survey(None, out=tmp_path, register=reg, seed=1)
    (tmp_path / "archive").mkdir()
    assert question_main(["prepare", "--archive", str(tmp_path / "archive"), "--register", str(tmp_path / "p2.jsonl"),
                          "--config", str(cfg.path), "--floor-ev", "0.1", "--floor-frequency", "10", "--sigma", "1.0",
                          "--sigma-provenance", "fixture"]) == 1
    assert "PROGRAMME STOPPED (M12.8): the author (author) stopped it" in capsys.readouterr().out
    assert register_main(["prepare", "--from-survey", str(tmp_path), "--grid", "g.toml", "--ids", "a", "--archive", str(tmp_path / "archive"),
                          "--register", str(tmp_path / "p2.jsonl"), "--config", str(cfg.path),
                          "--floor-ev", "0.1", "--floor-frequency", "10"]) == 1
    assert "PROGRAMME STOPPED (M12.8)" in capsys.readouterr().out


def test_the_conclusion_carries_the_survey_layer_and_passes_the_gate(tmp_path, capsys):
    reg = second_programme(tmp_path / "p2.jsonl")
    cfg = load(config_file(tmp_path))
    stop(cfg, reg, kind="author", by="author", reason="one verdict was the question")
    out = tmp_path / "docs" / "PROGRAMME-2-CONCLUSION.md"
    assert conclude_main(["--register", str(tmp_path / "p2.jsonl"), "--out", str(out), "--config", str(cfg.path)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "conclusion:" in capsys.readouterr().out
    assert text.startswith("# Programme conclusion — what 1 verdict established")
    assert "the author (author) stopped it: one verdict was the question — record `#9`" in text
    # the scoreboard, by record number
    assert "| axis | regime |" in text and "| outcome | **supported** (#6) |" in text and "| alpha spent | 0.4000 (#2) |" in text
    assert "| origin | survey cell `cell0123456789ab` of results `rrrrrrrrrrrr`, 32 cells screened |" in text
    assert "| beats-null | passed |" in text and "| leave-one-out | passed |" in text
    # the survey layer: cells screened, questions from it, shrinkage, eras
    assert "`grid-t`, grid `gggggggggggg`, seed 7: 32 cells over etfs" in text and "Questions registered from it: `Q2-001` (cell `cell0123456789ab`)" in text
    assert "Cells screened: 32 across 1 survey(s), stamped on every question registered from them (32 in all, N6); questions registered: 1; verdicts: 1." in text
    assert "No forward window was opened; no Strategy passed MEASURED." in text   # the fixture records no FORWARD transition
    assert "| `Q2-001` | `cell0123456789ab` | 32 | +0.314 | +0.210 | -0.104 | +0.428 | +0.260 | -0.168 | supported (#8) |" in text
    assert "70 at +0.200 / 70 at +0.250 / 70 at +0.180; each held out +0.215, +0.190, +0.225; 1 missed (#7)" in text
    assert "**`Q2-001` resolved supported** (#6). after two lower closes, a fixture name reverts. On `etfs` (AAA, BBB, CCC)" in text
    assert "Every check passed." in text
    # the author's build shows budgets, labelled; money never reaches the page; the author's sections are left to the author
    assert "0.4000 of the 0.50 declared on regime" in text and "The falsifier was declared as 3 null mechanism verdicts" in text
    assert all(str(v) not in text for v in MONEY.values())
    assert "31 of the 32 cells screened" in text and "The reserve was never looked at" in text
    assert text.count("*The author's, written on adoption. The Register does not choose.*") == 3
    pp = prepublish()
    assert pp.check_page(text, name="conclusion") == []
    # never overwritten
    assert conclude_main(["--register", str(tmp_path / "p2.jsonl"), "--out", str(out)]) == 1
    assert "never overwritten" in capsys.readouterr().out and out.read_text(encoding="utf-8") == text


def test_programme_one_concludes_from_its_lab_closed_record(tmp_path, capsys):
    out = tmp_path / "p1.md"
    assert conclude_main(["--register", str(ROOT / "register" / "register.jsonl"), "--out", str(out)]) == 0
    text = out.read_text(encoding="utf-8")
    assert "what 3 verdicts established" in text and "the lab's falsifier fired on 3 null mechanism verdicts (Q-003, Q-004, Q-005) (ADR-0033) — record `#33`" in text
    assert "| outcome | **null** (#9) | **null** (#21) | **null** (#32) |" in text
    assert "Refused: beats-null (random entry under the same geometry does as well); floor (" in text and "Passed: plateau." in text
    assert "No survey was recorded; every question came from a Draft." in text and "plain build" in text
    assert prepublish().check_page(text, name="p1") == []


def test_the_console_and_the_programme_page_show_the_stop(tmp_path):
    reg = fixture_register(tmp_path / "p1.jsonl", resolved=False)
    cfg = load(config_file(tmp_path))
    stop(cfg, reg, kind="author", by="author", reason="enough for one programme")
    f = gather(tmp_path / "p1.jsonl", controls="none", generated="g", repo_sha="x")
    assert f.stopped and f.stopped["kind"] == "author" and not f.lab_closed
    page = render(f)
    assert "The programme stopped: the author (author) stopped it: enough for one programme" in page
    assert "programme stopped · author · by author · enough for one programme · 1 questions, 0 surveys, 0 verdicts" in page
    page2, progs = build((tmp_path / "p1.jsonl",), generated="g", repo_sha="x")
    assert progs[0].stopped and ">Stopped<" in page2 and "python -m occams conclude" in page2


def test_a_question_refused_at_measurement_carries_the_refusals_evidence_into_the_scoreboard(tmp_path, capsys):
    """M14.5: no verdict, but the reader sees why — the refusal's reason and its numbers, by record number."""
    from tests.test_console import refused_at_measurement_register

    reg = refused_at_measurement_register(tmp_path / "p3.jsonl")
    cfg = load(config_file(tmp_path))
    stop(cfg, reg, kind="author", by="author", reason="the one question the numbers could buy was refused at measurement")
    out = tmp_path / "c.md"
    assert conclude_main(["--register", str(tmp_path / "p3.jsonl"), "--out", str(out), "--config", str(cfg.path)]) == 0
    text = out.read_text()
    assert "what 0 verdicts established" in text and "registered, refused at measurement, unresolved — the winning cell holds fewer trades" in text
    assert "(n 863, required_n 1,068; #3)" in text and "No verdict." in text
