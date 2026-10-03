"""The two author-facing tools: ``occams ingest`` (M4.1 through the port,
no network in tests) and ``occams spread`` (M5.0's observations and the
measured spread the cost model accepts)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from occams.costs.equity import EquityCosts, InstrumentClass
from occams.data.archive import BarArchive
from occams.ingest import main as ingest_main
from occams.spread import load, record, summarise
from occams.spread import main as spread_main

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "tiingo_synthetic.json"


def test_ingest_from_the_fixture_archives_and_charges_the_budget(tmp_path, capsys):
    rc = ingest_main(["XSYN", "YSYN", "--start", "2024-01-01", "--end", "2024-12-31",
                      "--archive", str(tmp_path / "a"), "--fixture", str(FIXTURE)])
    out = capsys.readouterr().out
    assert rc == 0 and "XSYN: 80 bars" in out and "budget used this month: 2/500" in out
    assert len(BarArchive(tmp_path / "a").entries()) == 2


def test_a_second_ingest_of_an_archived_span_does_not_call_the_source(tmp_path, capsys, monkeypatch):
    from occams import ingest as ingest_mod
    calls = []
    real = ingest_mod.FixtureSource.fetch

    def counting(self, symbol, start, end):
        calls.append(symbol)
        return real(self, symbol, start, end)

    monkeypatch.setattr(ingest_mod.FixtureSource, "fetch", counting)
    args = ["XSYN", "--start", "2024-01-02", "--end", "2024-04-23", "--archive", str(tmp_path / "a"), "--fixture", str(FIXTURE)]
    assert ingest_mod.main(args) == 0 and calls == ["XSYN"]
    assert ingest_mod.main(args) == 0 and calls == ["XSYN"]  # covered: not fetched again
    assert "already archived" in capsys.readouterr().out
    assert ingest_mod.main(args + ["--refresh"]) == 0 and calls == ["XSYN", "XSYN"]
    assert len(list((tmp_path / "a" / "bars").iterdir())) == 1  # identical content: same hash, no second file
    assert len(BarArchive(tmp_path / "a").entries()) == 2      # but the manifest notes that it was asked for again


def test_a_vendor_history_that_starts_after_the_requested_start_still_counts_as_covered(tmp_path):
    """SPY's first bar is 1993-01-29; a request from 1993-01-01 must not be
    re-fetched forever because the vendor has nothing earlier. The manifest
    records what was asked for, and coverage is judged on that."""
    from datetime import date
    ingest_main(["XSYN", "--start", "2023-06-01", "--end", "2024-04-23", "--archive", str(tmp_path / "a"), "--fixture", str(FIXTURE)])
    a = BarArchive(tmp_path / "a")
    e = a.latest_for("XSYN")
    assert e["first_at"][:10] == "2024-01-02" and e["requested_start"] == "2023-06-01"
    assert a.covers("XSYN", date(2023, 6, 1), date(2024, 4, 23)) is not None
    assert a.covers("XSYN", date(2023, 1, 1), date(2024, 4, 23)) is None  # an earlier start was never asked for


def test_an_uncovered_span_is_fetched(tmp_path):
    from occams.data.archive import BarArchive as A
    ingest_main(["YSYN", "--start", "2024-01-02", "--end", "2024-02-15", "--archive", str(tmp_path / "a"), "--fixture", str(FIXTURE)])
    a = A(tmp_path / "a")
    from datetime import date
    assert a.covers("YSYN", date(2024, 1, 2), date(2024, 2, 15)) is not None
    assert a.covers("YSYN", date(2024, 1, 2), date(2024, 4, 23)) is None  # the later span is not held


def test_ingest_refuses_a_symbol_the_fixture_lacks_and_reports_it(tmp_path, capsys):
    rc = ingest_main(["NOPE", "--start", "2024-01-01", "--end", "2024-12-31", "--archive", str(tmp_path / "a"),
                      "--fixture", str(FIXTURE)])
    assert rc == 1 and "REFUSED" in capsys.readouterr().out


def test_the_live_ingest_refuses_without_the_key(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    rc = ingest_main(["SPY", "--start", "2024-01-01", "--end", "2024-01-31", "--archive", str(tmp_path / "a")])
    assert rc == 1 and "TIINGO_API_KEY" in capsys.readouterr().out


def test_spread_observations_go_to_a_local_file_only(tmp_path):
    with pytest.raises(ValueError, match="gitignored"):
        record(tmp_path / "spread.jsonl", instrument="X", bid=99.99, ask=100.01, phase="open")
    p = tmp_path / "spread.local.jsonl"
    record(p, instrument="X", bid=99.99, ask=100.01, phase="open", at="2026-09-11T13:31:00+00:00")
    assert load(p)[0].fraction == pytest.approx(0.0002, abs=1e-6)
    with pytest.raises(ValueError):
        record(p, instrument="X", bid=100.01, ask=99.99, phase="open")


def test_summarise_refuses_until_all_three_phases_then_feeds_the_cost_model(tmp_path):
    p = tmp_path / "spread.local.jsonl"
    record(p, instrument="X", bid=99.99, ask=100.01, phase="open", at="t1")
    record(p, instrument="Y", bid=49.98, ask=50.02, phase="mid", at="t2")
    with pytest.raises(ValueError, match="phases"):
        summarise(p, provenance="demo account, fixture")
    record(p, instrument="X", bid=100.00, ask=100.03, phase="close", at="t3")
    out = summarise(p, provenance="demo account, fixture")
    assert out["basis"] == "measured" and out["observations"] == 3 and set(out["phases"]) == {"open", "mid", "close"}
    written = json.loads(p.with_suffix(".measurement.json").read_text())
    assert written["fraction"] == pytest.approx(out["fraction"])
    costs = EquityCosts.declared(InstrumentClass.US_LARGE, instrument_currency="USD", account_currency="USD")
    measured = costs.with_measured(load(p), provenance="demo account, fixture")
    assert measured.basis == "measured" and measured.bound() is measured
    assert measured.spread.fraction < costs.bound().spread.fraction  # the bound was the worst end of the range


def test_spread_cli(tmp_path, capsys):
    p = tmp_path / "s.local.jsonl"
    for ph, b, a in (("open", 99.99, 100.01), ("mid", 99.98, 100.02), ("close", 99.99, 100.02)):
        assert spread_main(["record", str(p), "--instrument", "X", "--bid", str(b), "--ask", str(a), "--phase", ph]) == 0
    assert spread_main(["summarise", str(p), "--provenance", "demo account 2026-09-11"]) == 0
    assert "measured spread" in capsys.readouterr().out
    assert spread_main(["record", str(tmp_path / "bad.jsonl"), "--instrument", "X", "--bid", "1", "--ask", "2", "--phase", "open"]) == 2
