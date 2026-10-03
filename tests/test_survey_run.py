"""M12.3 — the batch survey runner: definition partition only, seeded, resumable, recorded at zero alpha."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from occams.data.partitions import Partitions, freeze_calendar
from occams.proposers.regime import ClusterLevel, freeze
from occams.register import Register
from occams.survey.grid import load as load_grid
from occams.survey.run import SurveyRefused, engine_code_sha, main as run_main, record_survey, run_survey
from occams.universe import main as universe_main
from tests.test_calendar import latest
from tests.test_console import config_on_disk
from tests.test_programme2 import archive

SMALL = '''
[grid]
name = "grid-t"
programme = 2
declared_on = "2026-09-12"
partition = "definition"
side = "long"
baseline = "always_long"
[universes.etfs]
subject = "a fixture name"
regime_index = "AAA"
[regimes]
labels = ["none", "up"]
[horizons]
default = "multi_day"
[geometry]
holds = [1, 3]
targets = [0, 2]
[[geometry.stops]]
kind = "percent"
values = [2, 3]
[[mechanisms]]
kind = "down_run"
order = "market"
params = [{ runs = 2 }, { runs = 3 }]
'''


def world(tmp_path, *, classifier=True):
    a = archive(tmp_path / "archive")
    cfg = config_on_disk(tmp_path)
    reg_path = tmp_path / "p2.jsonl"
    assert universe_main(["declare", "--register", str(reg_path), "--name", "etfs", "--members", "AAA,BBB,CCC", "--rule", "fixture",
                          "--bias", "none", "--chosen-on", "2026-09-12"]) == 0
    reg = Register(reg_path)
    freeze_calendar(reg, latest(a), split=Partitions.from_config(cfg), config_sha="c", reason="fixture", universe="etfs")
    if classifier:
        freeze(a, cfg, register=reg, level=ClusterLevel.INDEX, index_name="AAA", seed=1, config_sha="c", universe="etfs", names=("AAA",))
    grid_path = tmp_path / "grid-t.toml"
    grid_path.write_text(SMALL)
    return a, cfg, reg, load_grid(grid_path, register=reg, plateau_cells=4)


@pytest.mark.slow
def test_a_complete_run_records_the_survey_and_the_same_grid_twice_is_byte_identical(tmp_path):
    a, cfg, reg, grid = world(tmp_path)
    assert grid.count == 32
    out = tmp_path / "out"
    r1 = run_survey(grid, archive=a, register=reg, cfg=cfg, out=out, seed=7, workers=1, log=lambda *_: None)
    assert r1["recorded"] and r1["cell_count"] == 32 and len(list((out / "cells").glob("*.json"))) == 32
    rec = [r for r in reg.records() if r["type"] == "SurveyRecorded"]
    assert len(rec) == 1 and rec[0]["grid_sha"] == grid.sha and rec[0]["results_sha"] == r1["results_sha"] and rec[0]["seed"] == 7
    assert rec[0]["classifier_hash"] and rec[0]["calendars"][0][0] == "etfs"
    digests = {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in (out / "cells").glob("*.json")}
    # a second run over the same out directory recomputes nothing and records nothing new
    r2 = run_survey(grid, archive=a, register=reg, cfg=cfg, out=out, seed=7, workers=1, log=lambda *_: None)
    assert r2["results_sha"] == r1["results_sha"] and not r2["recorded"]
    assert sum(1 for r in reg.records() if r["type"] == "SurveyRecorded") == 1
    # a fresh out directory gives byte-identical cell files
    r3 = run_survey(grid, archive=a, register=reg, cfg=cfg, out=tmp_path / "out2", seed=7, workers=1, log=lambda *_: None)
    assert r3["results_sha"] == r1["results_sha"]
    assert {f.name: hashlib.sha256(f.read_bytes()).hexdigest() for f in (tmp_path / "out2" / "cells").glob("*.json")} == digests
    # a different seed is a different survey, and records
    r4 = run_survey(grid, archive=a, register=reg, cfg=cfg, out=tmp_path / "out3", seed=8, workers=1, log=lambda *_: None)
    assert r4["recorded"] and sum(1 for r in reg.records() if r["type"] == "SurveyRecorded") == 2


def test_a_cell_file_says_what_was_asked_what_it_showed_and_what_it_would_cost(tmp_path):
    a, cfg, reg, grid = world(tmp_path)
    out = tmp_path / "out"
    run_survey(grid, archive=a, register=reg, cfg=cfg, out=out, seed=7, workers=1, log=lambda *_: None)
    cells = [json.loads(f.read_text()) for f in (out / "cells").glob("*.json")]
    gated = next(c for c in cells if c["regime"] == "up")
    plain = next(c for c in cells if c["regime"] == "none" and c["target"] == 2.0)
    for c in (gated, plain):
        assert c["partition"]["name"] == "definition" and c["partition"]["names"] == ["AAA", "BBB", "CCC"] and c["seed"] == 7
        assert c["baseline"]["trades"] >= c["trades"] >= 0 and "always" not in c["hypothesis"]
        assert len(c["eras"]) == 3 and len(c["leave_one_era_out"]) == 3 and c["readiness"]["names_ok"] and c["readiness"]["plateau_ok"]
        assert c["n_raw_measurement"] >= c["n_eff_measurement"] >= 0 and c["measurement_days"] > 0
        assert set(c["lowest_affordable_floor"]) == {"4", "9"} and "elapsed" not in json.dumps(c)
    assert gated["classifier"] and gated["axis"] == "regime" and "inside the up regime" in gated["hypothesis"]
    assert plain["classifier"] == "" and plain["axis"] == "price_daily" and plain["spec_hash"] != gated["spec_hash"]
    index = json.loads((out / "survey.json").read_text())
    assert index["cell_count"] == 32 and len(index["cells"]) == 32 and index["universes"]["etfs"]["measurement_days"] > 0
    row = next(r for r in index["cells"] if r["cell"] == plain["cell"])
    assert set(row["axis_sensitivity"]) <= {"hold", "stop", "target"} and row["baseline_ev_net"] == plain["baseline"]["ev_net"]


def test_a_killed_run_resumes_without_recomputing_a_finished_cell(tmp_path):
    a, cfg, reg, grid = world(tmp_path)
    out = tmp_path / "out"
    run_survey(grid, archive=a, register=reg, cfg=cfg, out=out, seed=7, workers=1, limit=10, log=lambda *_: None)
    assert len(list((out / "cells").glob("*.json"))) == 10 and not [r for r in reg.records() if r["type"] == "SurveyRecorded"]
    before = {f.name: f.stat().st_mtime_ns for f in (out / "cells").glob("*.json")}
    lines = []
    res = run_survey(grid, archive=a, register=reg, cfg=cfg, out=out, seed=7, workers=1, log=lines.append)
    assert res["recorded"] and any("22 computed, 10 already there" in ln for ln in lines)
    assert all((out / "cells" / n).stat().st_mtime_ns == t for n, t in before.items())   # untouched, not rewritten
    # a file from another seed in the same directory is recomputed, not trusted
    victim = next((out / "cells").glob("*.json"))
    victim.write_text(json.dumps({"grid_sha": grid.sha, "seed": 99}))
    lines.clear()
    run_survey(grid, archive=a, register=reg, cfg=cfg, out=out, seed=7, workers=1, log=lines.append)
    assert any("1 computed, 31 already there" in ln for ln in lines)


def test_a_cell_is_stamped_with_the_engines_code_not_the_commit(tmp_path):
    a, cfg, reg, grid = world(tmp_path)
    out = tmp_path / "out"
    res = run_survey(grid, archive=a, register=reg, cfg=cfg, out=out, seed=7, workers=1, log=lambda *_: None)
    c = json.loads(next((out / "cells").glob("*.json")).read_text())
    assert c["engine_code_sha"] == engine_code_sha() and len(c["engine_code_sha"]) == 16 and "engine_sha" not in c
    assert res["engine_shas"]["engine_code_sha"] == engine_code_sha() and "position_boxed" in res["engine_shas"]
    from occams import identity

    root = Path(__file__).resolve().parent.parent
    files = identity.closure()                 # M16.10: the import closure of the modules that measure, not a list kept by hand
    assert all((root / f).exists() for f in files) and "occams/survey/run.py" in files and "occams/core/execution.py" in files
    assert engine_code_sha() == identity.code_closure_sha()
    assert "-dirty" not in c["engine_code_sha"] and not any(ch in "-g" for ch in c["engine_code_sha"] if ch == "-")


@pytest.mark.slow
def test_the_runner_never_requests_the_measurement_slice(tmp_path, monkeypatch):
    a, cfg, reg, grid = world(tmp_path)
    asked = []
    original = Partitions.slice

    def spy(self, bars, partition, *, span=None):
        asked.append(partition)
        return original(self, bars, partition, span=span)

    monkeypatch.setattr(Partitions, "slice", spy)
    run_survey(grid, archive=a, register=reg, cfg=cfg, out=tmp_path / "out", seed=7, workers=1, log=lambda *_: None)
    assert asked and set(asked) == {"definition"}
    src = (Path(__file__).resolve().parent.parent / "occams" / "survey" / "run.py").read_text()
    assert 'slice(' in src and '"measurement"' in src.replace('["measurement"]', "")  is False or 'slice(bars[m], "definition"' in src


def test_a_fill_the_auditor_refuses_is_a_missed_trade_counted_in_the_cell_not_a_refusal(tmp_path):
    from dataclasses import replace

    from occams.data.archive import BarArchive
    from occams.engine.day_boxed import NO_ACTIONS
    from tests.test_calendar import LO
    from tests.test_price_proposer import calendar_bars

    a = BarArchive(tmp_path / "archive")
    for i, n in enumerate(("AAA", "BBB", "CCC")):
        b = calendar_bars(n, first=LO, days=1200, seed=40 + i)
        if n == "BBB":   # one flat bar early in the definition partition: open == high == low, the halt auditor's rule
            j = 30
            b = replace(b, open=b.open[:j] + (b.close[j],) + b.open[j + 1:], high=b.high[:j] + (b.close[j],) + b.high[j + 1:],
                        low=b.low[:j] + (b.close[j],) + b.low[j + 1:])
        a.put(b, NO_ACTIONS, source_id="synthetic")
    cfg = config_on_disk(tmp_path)
    reg_path = tmp_path / "p2.jsonl"
    universe_main(["declare", "--register", str(reg_path), "--name", "etfs", "--members", "AAA,BBB,CCC", "--rule", "f", "--bias", "n",
                   "--chosen-on", "2026-09-12"])
    reg = Register(reg_path)
    freeze_calendar(reg, latest(a), split=Partitions.from_config(cfg), config_sha="c", reason="fixture", universe="etfs")
    grid_path = tmp_path / "grid-t.toml"
    grid_path.write_text(SMALL.replace('labels = ["none", "up"]', 'labels = ["none"]'))
    grid = load_grid(grid_path, register=reg, plateau_cells=4)
    lines = []
    res = run_survey(grid, archive=a, register=reg, cfg=cfg, out=tmp_path / "out", seed=7, workers=1, log=lines.append)
    assert res["recorded"] and res["cell_count"] == 16
    # ADR-0041: nothing is refused; the hold-1 baselines land an entry on the flat bar and miss it, the hold-3 baselines step over it
    assert res["cells_with_refused_baseline"] == {"etfs": 0} and res["refused_cells"] == {"etfs": 0}
    assert res["baselines_missed_trades"]["etfs"] == 8 and any("missed trades" in ln for ln in lines)
    cells = [json.loads(f.read_text()) for f in (tmp_path / "out" / "cells").glob("*.json")]
    hit = [c for c in cells if c["baseline"]["missed"]]
    assert len(hit) == 8 and all(c["hold"] == 1.0 for c in hit)
    assert all(c["baseline"]["missed"] == 1 and c["baseline"]["missed_by_name"] == {"BBB": 1} and c["baseline"]["refused"] == ""
               and c["margin_net"] is not None and c["baseline"]["trades"] > 0 for c in hit)
    assert all(c["baseline"]["missed"] == 0 for c in cells if c["hold"] == 3.0)
    assert all(c["refused"] == "" for c in cells)
    assert all(m["name"] == "BBB" and "did not trade" in m["reason"] for c in cells for m in c["missed_trades"])
    assert all(c["missed"] == len(c["missed_trades"]) == sum(c["missed_by_name"].values()) for c in cells)
    rows = json.loads((tmp_path / "out" / "survey.json").read_text())["cells"]
    assert sum(r["baseline_missed"] for r in rows) == 8 and all("missed" in r and "missed_by_name" in r for r in rows)


def test_gated_cells_wait_on_a_frozen_classifier_and_a_partial_run_records_nothing(tmp_path):
    a, cfg, reg, grid = world(tmp_path, classifier=False)
    lines = []
    res = run_survey(grid, archive=a, register=reg, cfg=cfg, out=tmp_path / "out", seed=7, workers=1, log=lines.append)
    assert not res["recorded"] and res["cell_count"] == 16 and any("wait on a ClassifierFrozen" in ln for ln in lines)
    assert not [r for r in reg.records() if r["type"] == "SurveyRecorded"]
    with pytest.raises(SurveyRefused, match="not in the grid"):
        run_survey(grid, archive=a, register=reg, cfg=cfg, out=tmp_path / "o", seed=7, universe="nope", log=lambda *_: None)


def test_a_run_elsewhere_is_recorded_here_by_the_record_step_after_verification(tmp_path, capsys):
    a, cfg, reg, grid = world(tmp_path)
    out = tmp_path / "out"
    res = run_survey(grid, archive=a, register=reg, cfg=cfg, out=out, seed=7, workers=1, record=False, log=lambda *_: None)
    assert not res["recorded"] and res["cell_count"] == 32 and res["platform"]["python"] and "machine" in res["platform"]
    assert not [r for r in reg.records() if r["type"] == "SurveyRecorded"]
    rec = record_survey(grid, out=out, register=reg, seed=7, log=lambda *_: None)
    assert rec["recorded"] and rec["results_sha"] == res["results_sha"]
    r = [x for x in reg.records() if x["type"] == "SurveyRecorded"][-1]
    assert r["cell_count"] == 32 and "computed on" in r["reason"] and "python 3." in r["reason"] and r["calendars"][0][0] == "etfs"
    assert not record_survey(grid, out=out, register=reg, seed=7, log=lambda *_: None)["recorded"]     # once
    with pytest.raises(SurveyRefused, match="not .* seed 8"):
        record_survey(grid, out=out, register=reg, seed=8)
    victim = next((out / "cells").glob("*.json"))
    victim.write_text(victim.read_text().replace('"seed":7', '"seed":7 '))       # a byte changed: the results hash moves
    with pytest.raises(SurveyRefused, match="do not match the index"):
        record_survey(grid, out=out, register=reg, seed=7)
    assert run_main(["record", str(tmp_path / "grid-t.toml"), "--out", str(out), "--register", str(reg.path), "--seed", "7"]) == 1
    assert "REFUSED" in capsys.readouterr().out


@pytest.mark.slow
def test_the_command_runs_in_parallel_and_records(tmp_path, capsys):
    a, cfg, reg, grid = world(tmp_path)
    rc = run_main([str(tmp_path / "grid-t.toml"), "--archive", str(tmp_path / "archive"), "--register", str(reg.path),
                   "--config", str(tmp_path / "occams.toml"), "--out", str(tmp_path / "out"), "--seed", "3", "--workers", "2"])
    out = capsys.readouterr().out
    assert rc == 0 and "SurveyRecorded appended" in out and "32 computed" in out
    assert run_main(["run", str(tmp_path / "grid-t.toml"), "--archive", str(tmp_path / "archive"), "--register", str(reg.path),
                     "--config", str(tmp_path / "occams.toml"), "--out", str(tmp_path / "out-nr"), "--seed", "3", "--no-record"]) == 0
    assert "not recorded here" in capsys.readouterr().out
    assert run_main([str(tmp_path / "grid-t.toml"), "--archive", str(tmp_path / "archive"), "--register", str(reg.path),
                     "--config", str(tmp_path / "occams.toml"), "--out", str(tmp_path / "out"), "--seed", "3", "--dry-run"]) == 0
    assert "32 cells" in capsys.readouterr().out


@pytest.mark.slow
def test_a_survey_reads_only_the_bars_its_grid_names_and_the_burst_uploads_only_those(tmp_path, capsys):
    """M14.7: the manifest is a chain and goes whole; the runner asks the archive for the grid's names and the
    classifier's index and nothing else, so a box holding only those bars runs the survey; `survey inputs` lists
    exactly what the burst uploads."""
    from dataclasses import fields

    from occams.data.archive import Archived, BarArchive, NotArchived
    from occams.survey.run import survey_inputs, survey_names

    a, cfg, reg, grid = world(tmp_path)
    assert survey_names(grid, reg) == {"AAA", "BBB", "CCC"}                      # the members; the index AAA is among them
    # a series the manifest names but the box does not hold: a survey must not need it
    e = a.latest_entries()["AAA"]
    ghost = {f.name: e[f.name] for f in fields(Archived)}
    ghost.update(name="ZZZ", sha="0" * 64)
    a.manifest.append(Archived(**ghost))
    with pytest.raises(NotArchived):
        a.latest_bars()                                                          # everything, strictly: the ghost is refused
    assert set(a.latest_bars(names=("AAA", "BBB"))) == {"AAA", "BBB"}            # only what is asked for is read
    with pytest.raises(NotArchived, match="ZZZ"):
        a.latest_bars(names=("AAA", "ZZZ"))
    res = run_survey(grid, archive=a, register=reg, cfg=cfg, out=tmp_path / "out", seed=7, workers=1, log=lambda *_: None)
    assert res["recorded"] and res["cell_count"] == 32
    paths = survey_inputs(grid, reg, BarArchive(tmp_path / "archive"))
    assert paths[0].name == "manifest.jsonl" and len(paths) == 4 and all(p.exists() for p in paths)
    capsys.readouterr()                                                          # the fixture's own prints
    assert run_main(["inputs", str(tmp_path / "grid-t.toml"), "--register", str(tmp_path / "p2.jsonl"),
                     "--archive", str(tmp_path / "archive")]) == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert [Path(x) for x in out] == paths
    from occams.survey.grid import main as survey_main                          # the same through `python -m occams survey inputs`
    assert survey_main(["inputs", str(tmp_path / "grid-t.toml"), "--register", str(tmp_path / "p2.jsonl"),
                        "--archive", str(tmp_path / "archive")]) == 0
    assert capsys.readouterr().out.strip().splitlines() == out
    with pytest.raises(NotArchived, match="nope"):
        a.bar_paths(["AAA", "nope"])
