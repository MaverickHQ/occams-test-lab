"""M12.4 — the survey page: static, both themes, trust not profit; the console's Surveys section."""

from __future__ import annotations

import pytest
import json
from pathlib import Path

from occams.console import build
from occams.survey.page import main as page_main, render_page, tier_of
from occams.survey.run import run_survey
from tests.test_survey_run import world

MONEY = ("987654", "1234.5", "4321", "8765", "ZZZ")


def survey(tmp_path):
    a, cfg, reg, grid = world(tmp_path)
    out = tmp_path / "out"
    run_survey(grid, archive=a, register=reg, cfg=cfg, out=out, seed=7, workers=1, log=lambda *_: None)
    return a, cfg, reg, grid, out


@pytest.mark.slow
def test_the_page_says_what_was_asked_on_what_what_it_showed_and_whether_it_is_registrable(tmp_path):
    a, cfg, reg, grid, out = survey(tmp_path)
    page = render_page(grid, out, register=reg, cfg=cfg, generated="g")
    assert "<script" not in page and "http" not in page.replace("http-equiv", "") and "prefers-color-scheme" in page
    assert "Register record <strong>#" in page and 'id="matrix"' in page and 'id="u-etfs"' in page and "down_run(runs=2) · market" in page
    assert "After 2 consecutive lower closes, a fixture name carries positive EV" in page      # the hypothesis in the proposer's words
    assert "era 1" in page and "without it" in page and "Every name held out" in page and "Registering it:" in page
    assert "the accountant prices it at <strong>" in page and "alpha on the price_daily axis" in page
    assert all(m not in page for m in MONEY) and "Nothing here is a verdict" in page and "Colour is trust, never profit" in page
    rows = json.loads((out / "survey.json").read_text())["cells"]
    assert {tier_of(r) for r in rows} <= {"held", "positive", "margin", "none", "refused"}
    unpriced = render_page(grid, out, register=None, cfg=None, generated="g")
    assert "prices it at registration" in unpriced and "Register record <strong>#" not in unpriced and "not yet a Register record" in unpriced


@pytest.mark.slow
def test_the_command_writes_the_page_and_refuses_another_grids_results(tmp_path, capsys):
    a, cfg, reg, grid, out = survey(tmp_path)
    html = tmp_path / "docs" / "surveys" / "x.html"
    rc = page_main([str(tmp_path / "grid-t.toml"), "--out", str(out), "--register", str(reg.path), "--config", str(tmp_path / "occams.toml"), "--html", str(html)])
    assert rc == 0 and html.exists() and "priced" in capsys.readouterr().out and html.read_text().startswith("<!doctype html>")
    other = tmp_path / "grid-o.toml"
    other.write_text((tmp_path / "grid-t.toml").read_text().replace('name = "grid-t"', 'name = "grid-o"'))
    assert page_main([str(other), "--out", str(out), "--html", str(tmp_path / "o.html")]) == 1
    assert "REFUSED" in capsys.readouterr().out


@pytest.mark.slow
def test_the_console_gains_a_surveys_section_that_links_to_the_page(tmp_path):
    a, cfg, reg, grid, out = survey(tmp_path)
    page, facts = build(reg.path, controls="none", generated="g", repo_sha="x")
    assert len(facts.surveys) == 1 and 'id="surveys"' in page and 'href="surveys/grid-t-seed7.html"' in page
    assert "Nothing in a survey is a verdict" in page and "Surveys (1)" in page
    src = (Path(__file__).resolve().parent.parent / "occams" / "survey" / "page.py").read_text()
    assert "<script" not in src and "urlopen" not in src and "capital" not in src
