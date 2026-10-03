"""M12.7 — the programme page: what did we search, what did it cost, what
did we find, for every programme, beside each other; a verdict is never
shown without the survey cell it came from; the publication gate's check
(M11.7) passes on it."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from occams.console.facts import AuthorView
from occams.console.programme import build, main as programme_main
from occams.ledger.alpha_budget import AlphaSpent, ObservationsConsumed
from occams.register import LabClosed, Register
from tests.test_console import E, MONEY, T, W, config_on_disk, fixture_register

ROOT = Path(__file__).resolve().parent.parent


def prepublish():
    spec = importlib.util.spec_from_file_location("_prepublish", ROOT / "tools" / "prepublish.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def second_programme(path: Path) -> Register:
    """A programme with a survey, a question registered from one of its cells, and a verdict."""
    reg = Register(path)
    reg.append(Register.UniverseDeclared("etfs", ("AAA", "BBB", "CCC"), "us_large", "tiingo-starter", "the fixture's three names",
                                         "2026-09-12", "none: synthetic", ""))
    reg.append(Register.SurveyRecorded("grid-t", "g" * 64, "r" * 64, 32, ("etfs",), (("etfs", 727592, 728192),), "c" * 64,
                                       {"engine_code_sha": "e" * 16}, 7, "out", "definition partition only; zero alpha"))
    reg.append(AlphaSpent("Q2-001", "regime", "mechanism", 0.1, 4, 0.4, 0.1, "cfg"))
    reg.append(Register.HypothesisRegistered("Q2-001", "mechanism", "regime", "after two lower closes, a fixture name reverts",
                                             "the winner at or below the null's corrected quantile", 0.1, 1.0, 4, 100, 300,
                                             0.4, "author", None, None, "cfg", False, 32, "r" * 64, "cell0123456789ab", "etfs"))
    reg.append(ObservationsConsumed("Q2-001", "regime", "measurement", 728192, 729392, ("AAA", "BBB", "CCC")))
    reg.append(Register.HypothesisMeasured("Q2-001", T, "position_boxed", E, 3, "measurement", 210, 4))
    reg.append(Register.HypothesisResolved("Q2-001", "supported", 0.21, 40.0, W, E, 3, "measurement", (), "bounded", T, (0, 1)))
    reg.append(Register.EraDecomposition("Q2-001", W, "measurement",
                                         ({"bounds": [728192, 728592], "n": 70, "ev_net": 0.2}, {"bounds": [728592, 728992], "n": 70, "ev_net": 0.25},
                                          {"bounds": [728992, 729392], "n": 70, "ev_net": 0.18}), (0.215, 0.19, 0.225), 1, {"BBB": 1}, 3))
    reg.append(Register.Shrinkage("Q2-001", "r" * 64, "cell0123456789ab", 32, 153, 0.314, 0.428, 210, 0.21, -0.05, 0.26, -0.104, -0.168))
    return reg


def test_the_page_answers_the_three_questions_for_both_programmes_and_never_shows_a_verdict_without_its_cell(tmp_path):
    fixture_register(tmp_path / "p1.jsonl")
    Register(tmp_path / "p1.jsonl").append(LabClosed(3, "null", ("Q-1", "Q-2", "Q-3")))
    second_programme(tmp_path / "p2.jsonl")
    page, progs = build((tmp_path / "p1.jsonl", tmp_path / "p2.jsonl"), generated="g", repo_sha="x")
    assert len(progs) == 2 and progs[0].lab_closed and not progs[1].lab_closed
    assert page.count("What did we search") == 2 and page.count("What did it cost") == 2 and page.count("What did we find") == 2
    assert page.count(">Closed<") == 1 and page.count(">Open<") == 1 and "Programme 1" in page and "Programme 2" in page
    # programme 1's verdict came from a Draft and says so; programme 2's names its survey cell beside the verdict
    assert "registered from a Draft, not from a survey" in page and "cell0123456789ab" in page and "32</td>" in page
    assert "cells screened, stamped on 1 question(s) (N6)" in page
    assert "Shrinkage from screening" in page and "the survey page" in page and "grid-t" in page
    assert "The lab closed" in page and "PROGRAMME-CONCLUSION.md" in page
    # plain build: spend, no budgets; author's build: budgets and the count
    assert "Plain build" in page and "Budget" not in page.split("Programme 2")[0].split("Alpha spent by axis")[1][:40]
    assert "<script" not in page and "http://" not in page and "https://" not in page and "@import" not in page
    assert all(m not in page for m in ("987654", "1234.5", "4321", "8765"))
    author = AuthorView.from_config(config_on_disk(tmp_path))
    page2, _ = build((tmp_path / "p1.jsonl", tmp_path / "p2.jsonl"), author=author, generated="g", repo_sha="x")
    assert "Author's build" in page2 and "Remaining" in page2 and "of 1 null mechanism verdict" in page2
    assert all(str(v) not in page2 for v in MONEY.values())                                    # money never reaches the page (R9, S7)


def test_the_command_writes_the_page_and_the_publication_gate_passes_on_it(tmp_path, capsys):
    fixture_register(tmp_path / "p1.jsonl")
    second_programme(tmp_path / "p2.jsonl")
    out = tmp_path / "docs" / "programme.html"
    assert programme_main(["--register", str(tmp_path / "p1.jsonl"), "--register", str(tmp_path / "p2.jsonl"), "--out", str(out)]) == 0
    text = capsys.readouterr().out
    assert "programme page:" in text and "P1 p1.jsonl" in text and "P2 p2.jsonl" in text and "1 survey(s)" in text
    pp = prepublish()
    assert pp.check_page(out.read_text(encoding="utf-8"), name="programme") == []
    assert pp.check_register((tmp_path / "p2.jsonl").read_text(encoding="utf-8"), name="p2") == []
    assert pp.main([str(out), str(tmp_path / "p1.jsonl"), str(tmp_path / "p2.jsonl")]) == 0
    assert "clean" in capsys.readouterr().out
    # a tampered Register is a failure, not a report
    (tmp_path / "p2.jsonl").write_text((tmp_path / "p2.jsonl").read_text().replace('"supported"', '"null"'), encoding="utf-8")
    assert programme_main(["--register", str(tmp_path / "p2.jsonl"), "--out", str(out)]) == 1
    assert "REFUSED: TamperedHistory" in capsys.readouterr().out


def test_the_questions_table_carries_each_questions_state(tmp_path):
    """M14.5: a question registered, refused at measurement and unresolved says so in the programme's table."""
    from tests.test_console import refused_at_measurement_register

    refused_at_measurement_register(tmp_path / "p3.jsonl")
    page, (prog,) = build((tmp_path / "p3.jsonl",), generated="g", repo_sha="x")
    assert prog.findings[0].state == "registered, refused at measurement, unresolved"
    assert "<th>State</th>" in page and "registered, refused at measurement, unresolved" in page and "No verdict yet" in page
