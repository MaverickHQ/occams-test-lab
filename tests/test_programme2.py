"""M12.0 — the second programme's arithmetic and its place beside the first."""

from __future__ import annotations

import pytest

from occams.console import build
from occams.data.archive import BarArchive
from occams.engine.day_boxed import NO_ACTIONS
from occams.loop import main as loop_main
from occams.question import main as question_main
from occams.register import LabClosed, Register
from occams.whatif import (BASE_RATES, CELLS, FLOORS_WIDE, SIGNAL_RATES, affordability, close_probability, derive,
                           main as whatif_main, universe_rho, universes)
from tests.test_calendar import LO, latest
from tests.test_console import config_on_disk
from tests.test_price_proposer import calendar_bars


def archive(root, names=("AAA", "BBB", "CCC")) -> BarArchive:
    a = BarArchive(root)
    for i, n in enumerate(names):
        a.put(calendar_bars(n, first=LO, days=1200, seed=40 + i), NO_ACTIONS, source_id="synthetic")
    return a


def test_the_falsifier_arithmetic_is_what_a_count_buys(tmp_path):
    assert close_probability(3, 0.20) == pytest.approx((1 - 0.8 * 0.2) ** 3)      # 0.59: three nulls, one-in-five real
    assert close_probability(3, 0.0) == 1.0 and close_probability(12, 0.5) < close_probability(3, 0.5)
    d = derive(config_on_disk(tmp_path))
    assert d["falsifier_count"] in d["p_close"] and set(d["p_close"][d["falsifier_count"]]) == set(BASE_RATES)
    assert all(d["p_close"][n][p] <= d["p_close"][n][q] for n in d["p_close"] for p in BASE_RATES for q in BASE_RATES if p >= q)


def test_universe_rho_is_the_same_day_icc_of_returns(tmp_path):
    a = archive(tmp_path / "archive")
    rho, m, days = universe_rho(latest(a))
    assert 0.0 <= rho <= 1.0 and m == pytest.approx(3.0) and days == 1199


def test_affordability_says_what_each_floor_costs_in_trades_and_never_reads_measurement(tmp_path):
    cfg = config_on_disk(tmp_path)
    a = archive(tmp_path / "archive")
    u = affordability(cfg, latest(a), span=(LO, LO + 1199), name="fixture")
    assert u["names"] == 3 and u["measurement_days"] == 600 and set(u["rates"]) == set(SIGNAL_RATES)
    for r, row in u["rates"].items():
        assert 0 < row["n_eff"] <= row["n_raw"]
        floors = [row["affordable_floor"][k] for k in CELLS]
        assert all(f is None or f in FLOORS_WIDE for f in floors)
    # more signals detect a lower (or equal) floor at every sweep size; a bigger sweep never detects a lower floor
    lo, hi = u["rates"][min(SIGNAL_RATES)], u["rates"][max(SIGNAL_RATES)]
    for k in CELLS:
        assert (hi["affordable_floor"][k] or 1) <= (lo["affordable_floor"][k] or 1)
    for row in u["rates"].values():
        assert (row["affordable_floor"][max(CELLS)] or 1) >= (row["affordable_floor"][min(CELLS)] or 1)


def test_the_whatif_command_prints_both_tables_with_an_archive(tmp_path, capsys):
    config_on_disk(tmp_path)
    archive(tmp_path / "archive")
    reg = Register(tmp_path / "r.jsonl")
    assert whatif_main([str(tmp_path / "occams.toml"), "--archive", str(tmp_path / "archive"), "--register", str(reg.path)]) in (0, 1)
    out = capsys.readouterr().out
    assert "Falsifier arithmetic" in out and "← declared" in out and "Universe affordability" in out and "archive: AAA, BBB, CCC" in out
    assert len(universes(config_on_disk(tmp_path), archive(tmp_path / "archive2"), reg)) == 1


def test_the_console_renders_a_second_programme_beside_the_first_and_marks_the_closed_one(tmp_path):
    from tests.test_console import fixture_register
    fixture_register(tmp_path / "p1.jsonl")
    Register(tmp_path / "p1.jsonl").append(LabClosed(3, "null", ("Q-1", "Q-2", "Q-3")))
    page, facts = build(tmp_path / "p1.jsonl", controls="none", generated="g", repo_sha="x", others=(tmp_path / "p2.jsonl",))
    assert "Programme 1" in page and "Programme 2" in page and page.count(">Closed<") == 1 and page.count(">Open<") == 1
    assert 'id="position-1"' in page and 'id="position-2"' in page and 'id="register-2"' in page
    assert "P1 Findings (1)" in page and "P2 Findings (0)" in page and facts.lab_closed


def test_question_and_loop_take_the_programmes_config(tmp_path, capsys):
    config_on_disk(tmp_path)
    archive(tmp_path / "archive")
    reg, queue = tmp_path / "p2.jsonl", tmp_path / "p2-queue.jsonl"
    rc = question_main(["prepare", "--archive", str(tmp_path / "archive"), "--register", str(reg), "--config", str(tmp_path / "occams.toml"),
                        "--axis", "price_daily", "--entry", "down_run", "--runs", "3", "--hold", "3", "--holds", "3,5", "--stops", "3,5",
                        "--floor-ev", "0.15", "--floor-frequency", "50", "--sigma", "1.2", "--sigma-provenance", "fixture", "--id", "Q-p"])
    assert rc in (0, 1) and "POWERED" in capsys.readouterr().out
    assert loop_main([str(reg), str(tmp_path / "archive"), str(queue), "--seed", "7", "--config", str(tmp_path / "occams.toml")]) == 0
