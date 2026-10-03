"""M12.2 — the survey grid: committed, hashed, loaded or refused by name; nothing runs."""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest

from occams.register import Register
from occams.spec.compile import to_engine
from occams.spec.spec import EntryKind, Horizon, OrderType, StopKind
from occams.survey.grid import GridRefused, grid_sha, load, main as survey_main, readiness, summary
from occams.universe import main as universe_main

GRID = Path(__file__).resolve().parent.parent / "surveys" / "grid-001.toml"
UNIVERSES = ("index_etfs", "sector_etfs", "dow_30", "sp_100")


def register_with(tmp_path, names=UNIVERSES) -> Register:
    reg = tmp_path / "p2.jsonl"
    for n in names:
        assert universe_main(["declare", "--register", str(reg), "--name", n, "--members", "AAA,BBB,CCC",
                              "--rule", "fixture", "--bias", "none: synthetic", "--chosen-on", "2026-09-12"]) == 0
    return Register(reg)


def variant(tmp_path, *edits: tuple[str, str]) -> Path:
    text = GRID.read_text()
    for old, new in edits:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    p = tmp_path / "grid-x.toml"
    p.write_text(text)
    return p


@pytest.mark.slow
def test_the_first_grid_loads_its_hash_is_its_bytes_and_its_count_is_the_declared_product(tmp_path):
    reg = register_with(tmp_path)
    g = load(GRID, register=reg, plateau_cells=4)
    assert g.sha == grid_sha(GRID) == hashlib.sha256(GRID.read_bytes()).hexdigest()
    assert g.name == "grid-001" and g.partition == "definition" and g.side == "long" and g.supersedes == ""
    # per universe × regime: breakouts 8 parameterisations × (5 holds × 6 stops × 3 target options, plus intraday:
    # 1 hold × 6 stops × 2 targets), the other five kinds 18 × 5 × 6 × 3; four universes × four regimes
    per = 8 * (5 * 6 * 3 + 1 * 6 * 2) + 18 * 5 * 6 * 3
    assert per == 2_436 and g.count == per * 16 == 38_976 == sum(1 for _ in g.cells())
    assert g.per_axis() == {"price_daily": per * 4, "regime": per * 12}
    assert all(sum(row.values()) == per * len(g.regimes) for row in g.counts().values()) and set(g.counts()) == set(UNIVERSES)
    assert len(g.families) == 16 * (8 * (2 * 2 + 2 * 1) + 18 * 2 * 2) == 1_920
    assert all(f.targets for f in g.families if f.horizon is Horizon.INTRADAY)   # intraday carries a target (plateau)
    assert {f.kind for f in g.families} == {EntryKind.BREAKOUT_HIGH, EntryKind.BREAKOUT_LOW, EntryKind.CLOSE_ABOVE_MA,
                                            EntryKind.CLOSE_BELOW_MA, EntryKind.DOWN_RUN, EntryKind.RETURN_BELOW,
                                            EntryKind.PULLBACK_IN_TREND}


@pytest.mark.slow
def test_a_cell_is_a_compiled_strategy_with_a_content_id_and_the_proposers_sentence(tmp_path):
    g = load(GRID, register=register_with(tmp_path))
    cells = list(g.cells())
    ids = {c.id for c in cells}
    assert len(ids) == len(cells)                      # every cell distinct by content
    low = next(c for c in cells if c.family.kind is EntryKind.BREAKOUT_LOW and c.family.horizon is Horizon.INTRADAY
               and c.family.regime == "up" and c.target == 2.0 and c.family.stop_kind is StopKind.ATR)
    spec = low.spec
    assert spec.order_type is OrderType.LIMIT and spec.stop.kind is StopKind.ATR and spec.stop.lookback == 14
    assert {x.kind.value for x in spec.exits} == {"time", "target_r"} and to_engine(spec).engine == "day_boxed"
    assert "buy-limit at the lowest low of the prior" in low.hypothesis and low.family.subject in low.hypothesis
    assert "ends at the close of the entry day" in low.hypothesis and "inside the up regime" in low.hypothesis and "SPY" in low.hypothesis
    assert "no regime gate" not in low.hypothesis            # the gate is the grid's to state; a gated cell never denies it
    dow = next(c for c in cells if c.family.universe == "dow_30" and c.family.kind is EntryKind.DOWN_RUN and c.family.regime == "none")
    assert "a Dow 30 constituent" in dow.hypothesis and "3 consecutive" in dow.hypothesis or "2 consecutive" in dow.hypothesis
    assert "regime" not in dow.hypothesis and dow.spec.regime is None and not dow.target and len(dow.spec.exits) == 1
    # the same cell content in another grid has the same id: the id carries no grid name
    g2 = load(variant(tmp_path, ('name = "grid-001"', 'name = "grid-x"')), register=register_with(tmp_path / "b"))
    assert next(g2.cells()).id == cells[0].id and g2.sha != g.sha


@pytest.mark.slow
def test_a_grid_is_refused_by_name(tmp_path):
    reg = register_with(tmp_path)
    cases = [
        (('partition = "definition"', 'partition = "measurement"'), "definition partition and nothing else"),
        (('kind = "down_run"', 'kind = "always"'), "not a grid kind"),
        (('kind = "pullback_in_trend"', 'kind = "gap_fade"'), "not on the closed entry enum"),
        (('params = [{ runs = 2 }, { runs = 3 }, { runs = 4 }]', 'params = [{ lookback = 3 }]'), "down_run: down_run declares"),
        (('order = "limit"', 'order = "stop"'), "breakout_low enters as limit/market"),
        (('labels = ["none", "up", "down", "ranging"]', 'labels = ["none", "sideways"]'), "regime label 'sideways'"),
        (('side = "long"', 'side = "short"'), "long-only"),
        (('params = [{ short = 5, long = 50 }, { short = 10, long = 100 }, { short = 20, long = 200 }]',
          'params = [{ short = 50, long = 5 }]'), "does not compile"),
    ]
    for edits, msg in cases:
        with pytest.raises(GridRefused, match=re.escape(msg)):
            load(variant(tmp_path, edits), register=reg, plateau_cells=4)
    with pytest.raises(GridRefused, match="no UniverseDeclared record"):
        load(GRID, register=register_with(tmp_path / "three", names=UNIVERSES[:3]))
    # a sweep that cannot hold the declared plateau is refused before anything runs (Q-004)
    tight = variant(tmp_path, ("holds = [1, 3, 5, 10, 20]", "holds = [5]"), ("values = [2, 3, 5]", "values = [3]"),
                    ("values = [1.5, 2, 3]", "values = [2]"), ("targets = [0, 2, 3]", "targets = [0]"))
    with pytest.raises(GridRefused, match="cannot fit the sweep"):
        load(tight, register=reg, plateau_cells=4)
    assert load(tight, register=reg).count > 0            # without a plateau size the guard is not applied, and show says so


@pytest.mark.slow
def test_gated_cells_wait_on_a_frozen_classifier_for_the_regime_index(tmp_path):
    reg = register_with(tmp_path)
    g = load(GRID, register=reg)
    assert readiness(g, reg) == {u: None for u in UNIVERSES}
    reg.append(reg.ClassifierFrozen("abc123def456", 20, 100, 0.02, "index", "SPY", 1, 2, "", "", ("SPY",), 0.9, {}, 1, "cfg"))
    assert readiness(g, reg) == {u: "abc123def456" for u in UNIVERSES}


@pytest.mark.slow
def test_the_command_prints_the_hash_and_the_count_before_anything_runs(tmp_path, capsys):
    reg = register_with(tmp_path)
    assert survey_main(["show", str(GRID), "--register", str(reg.path)]) == 0
    out = capsys.readouterr().out
    assert grid_sha(GRID)[:12] in out and "cells 38,976" in out and "| sp_100 |" in out and "nothing runs here" in out
    assert "every family's sweep holds a plateau" in out and "wait on a ClassifierFrozen" in out
    assert survey_main(["cells", str(GRID), "--register", str(reg.path), "--universe", "sp_100", "--regime", "ranging", "--limit", "3"]) == 0
    out = capsys.readouterr().out
    assert out.count("sp_100 · ranging") == 3 and "3 of 38,976 cells shown" in out
    assert survey_main(["show", str(variant(tmp_path, ('side = "long"', 'side = "short"'))), "--register", str(reg.path)]) == 1
    assert "REFUSED" in capsys.readouterr().out
    assert "nothing runs here" in "\n".join(summary(load(GRID, register=reg), reg))


def test_the_grid_module_writes_nothing():
    src = (Path(__file__).resolve().parent.parent / "occams" / "survey" / "grid.py").read_text()
    assert ".append(" not in src and "write_text" not in src and "write_bytes" not in src and '"w"' not in src
    assert "measurement" not in src.replace("measurement partition", "")  # the runner's partition is not this module's business
