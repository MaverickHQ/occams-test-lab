"""M15.5 — your own bars: a CSV per symbol, ingested under a rights record you declare; refused without one;
then the same archive, the same universe, calendar, classifier and survey as any other series."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from occams.data.archive import BarArchive
from occams.data.bars import random_walk
from occams.ingest import main as ingest_main


def write_csvs(root: Path, names=("AAA", "BBB", "CCC"), *, days: int = 900) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    base = date(2015, 1, 2).toordinal()                              # a fixture's day is an index; a CSV carries dates
    for i, n in enumerate(names):
        b = random_walk(n, days=days, seed=11 + i, sigma_daily=0.01)
        lines = ["date,open,high,low,close,volume,dividend"]
        for j in range(b.n):
            d = date.fromordinal(base + b.day[j]).isoformat()
            lines.append(f"{d},{b.open[j]:.4f},{b.high[j]:.4f},{b.low[j]:.4f},{b.close[j]:.4f},{b.volume[j]:.0f},{'0.5' if j == 400 else ''}")
        (root / f"{n}.csv").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return root


def test_a_csv_is_ingested_only_under_a_declared_rights_record_and_never_charged_to_the_vendors_budget(tmp_path, capsys):
    csvs = write_csvs(tmp_path / "bars")
    common = ["AAA", "BBB", "--csv", str(csvs), "--start", "1900-01-01", "--end", "2100-01-01", "--archive", str(tmp_path / "archive")]
    # no rights, no ingest
    assert ingest_main([*common, "--source-id", "mine"]) == 1
    assert "rights-provenance" in capsys.readouterr().out
    assert ingest_main([*common, "--source-id", "mine", "--rights-provenance", "my export", "--permit", "internal_reproduction"]) == 1
    out = capsys.readouterr().out
    assert "does not permit private_retention" in out and "REFUSED" in out
    assert not (tmp_path / "archive" / "manifest.jsonl").exists() or BarArchive(tmp_path / "archive").latest_entries() == {}
    # declared: archived, with the rights beside the bars and no budget charge
    assert ingest_main([*common, "--source-id", "mine", "--rights-provenance", "my broker's export, mine to keep and analyse",
                        "--permit", "private_retention,internal_reproduction"]) == 0
    out = capsys.readouterr().out
    assert "rights for mine recorded in the archive as rights/" in out and "raw_redistribution forbidden" in out
    assert "your own bars, no budget charge" in out and "AAA: 900 bars, 1 actions" in out
    a = BarArchive(tmp_path / "archive")
    assert set(a.latest_entries()) == {"AAA", "BBB"} and all(e["source_id"] == "mine" for e in a.latest_entries().values())
    assert not (tmp_path / "archive" / "symbol-budget.json").exists()
    # a CSV without the full OHLC is refused by name
    (csvs / "DDD.csv").write_text("date,close\n2020-01-02,1\n", encoding="utf-8")
    assert ingest_main(["DDD", *common[2:], "--source-id", "mine", "--rights-provenance", "x", "--permit", "private_retention"]) == 1
    assert "lacks the column(s)" in capsys.readouterr().out


@pytest.mark.slow
def test_a_survey_and_a_question_run_on_your_own_bars(tmp_path, capsys):
    from occams.config import load
    from occams.data.partitions import Partitions, freeze_calendar
    from occams.proposers.regime import ClusterLevel, freeze
    from occams.register import Register
    from occams.survey.grid import load as load_grid
    from occams.survey.run import run_survey
    from occams.universe import main as universe_main
    from tests.test_calendar import latest
    from tests.test_console import config_on_disk
    from tests.test_survey_run import SMALL

    csvs = write_csvs(tmp_path / "bars", days=2400)
    assert ingest_main(["AAA", "BBB", "CCC", "--csv", str(csvs), "--start", "1900-01-01", "--end", "2100-01-01", "--archive",
                        str(tmp_path / "archive"), "--source-id", "mine", "--rights-provenance", "mine", "--permit",
                        "private_retention,internal_reproduction"]) == 0
    a = BarArchive(tmp_path / "archive")
    cfg = load(config_on_disk(tmp_path).path)
    reg_path = tmp_path / "programme-9.jsonl"
    assert universe_main(["declare", "--register", str(reg_path), "--name", "etfs", "--members", "AAA,BBB,CCC", "--rule", "my bars",
                          "--bias", "none", "--chosen-on", "2026-09-26"]) == 0
    reg = Register(reg_path)
    freeze_calendar(reg, latest(a), split=Partitions.from_config(cfg), config_sha="c", reason="csv", universe="etfs")
    freeze(a, cfg, register=reg, level=ClusterLevel.INDEX, index_name="AAA", seed=1, config_sha="c", universe="etfs", names=("AAA",))
    grid_path = tmp_path / "grid-t.toml"
    grid_path.write_text(SMALL)
    grid = load_grid(grid_path, register=reg, plateau_cells=4)
    res = run_survey(grid, archive=a, register=reg, cfg=cfg, out=tmp_path / "out", seed=7, workers=1, log=lambda *_: None)
    assert res["recorded"] and res["cell_count"] == 32
