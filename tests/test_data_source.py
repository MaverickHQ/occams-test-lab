"""M4.1 the DataSource port · M4.8 the archive · M4.9 rights (S9)."""

from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path

import pytest

from occams.data.actions import ActionKind
from occams.data.archive import BarArchive, NotArchived
from occams.data.rights import REGISTRY, Answer, Rights, RightsRefused, Use, require
from occams.data.source import (BudgetExceeded, FixtureSource, RateLimited, SourceError, SymbolBudget, TiingoSource,
                                export, ingest, parse_tiingo)

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "tiingo_synthetic.json"
JAN, DEC = date(2024, 1, 1), date(2024, 12, 31)


def test_bars_load_offline_from_the_committed_fixture():
    rows = FixtureSource(FIXTURE).fetch("XSYN", JAN, DEC)
    bars, actions = parse_tiingo("XSYN", rows)
    assert bars.n == 80 and bars.close_at is not None and bars.close_at[0].endswith("+00:00")
    kinds = [a.kind for a in actions.actions]
    assert ActionKind.SPLIT in kinds and ActionKind.DIVIDEND in kinds


def test_as_printed_ohlc_is_the_raw_columns_not_the_adjusted_ones():
    rows = FixtureSource(FIXTURE).fetch("XSYN", JAN, DEC)
    rows[5]["adjClose"] = 1.0  # a restated adjusted column must not move an as-printed bar
    bars, _ = parse_tiingo("XSYN", rows)
    assert bars.close[5] == rows[5]["close"] != 1.0


def test_full_ohlc_is_required():
    rows = FixtureSource(FIXTURE).fetch("YSYN", JAN, DEC)
    del rows[3]["low"]
    with pytest.raises(SourceError, match="full OHLC"):
        parse_tiingo("YSYN", rows)


def test_ingest_refuses_a_source_without_recorded_rights(tmp_path):
    class Unknown:
        source_id = "mystery-vendor"

        def fetch(self, *a):
            raise AssertionError("never reached: rights are checked before the fetch")

    with pytest.raises(RightsRefused, match="no recorded rights"):
        ingest(Unknown(), "XSYN", JAN, DEC, archive=BarArchive(tmp_path / "a"), budget=None, month="2026-09")


def test_ingest_archives_and_charges_the_budget(tmp_path):
    budget = SymbolBudget(tmp_path / "budget.json", limit=500)
    got = ingest(FixtureSource(FIXTURE), "XSYN", JAN, DEC, archive=BarArchive(tmp_path / "a"), budget=budget, month="2026-09")
    assert len(got.sha) == 64 and budget.used("2026-09") == ["XSYN"]
    assert got.rights.source_id == "synthetic"


def test_the_501st_unique_symbol_in_a_month_is_refused(tmp_path):
    budget = SymbolBudget(tmp_path / "budget.json", limit=3)
    for s in ("A", "B", "C", "A"):
        budget.charge(s, "2026-09")
    with pytest.raises(BudgetExceeded):
        budget.charge("D", "2026-09")
    budget.charge("D", "2026-10")  # a new month, a new budget


def test_the_live_source_has_no_key_and_no_default(monkeypatch):
    monkeypatch.delenv("TIINGO_API_KEY", raising=False)
    with pytest.raises(SourceError, match="TIINGO_API_KEY"):
        TiingoSource().fetch("XSYN", JAN, DEC)


def test_the_vendors_http_error_is_a_refusal_by_name_and_never_carries_the_token(monkeypatch):
    import io
    import urllib.error
    import urllib.request

    monkeypatch.setenv("TIINGO_API_KEY", "placeholder-value")

    def refuse(req, timeout):
        raise urllib.error.HTTPError(req.full_url, 404, "Not Found", {}, io.BytesIO(b'{"detail": "Not found."}'))

    monkeypatch.setattr(urllib.request, "urlopen", refuse)
    with pytest.raises(SourceError, match=r"XDEAD: the source answered HTTP 404") as e:
        TiingoSource().fetch("XDEAD", JAN, DEC)
    assert "Not found." in str(e.value) and "placeholder-value" not in str(e.value) and "Token" not in str(e.value)

    def unreachable(req, timeout):
        raise urllib.error.URLError("name resolution failed")

    monkeypatch.setattr(urllib.request, "urlopen", unreachable)
    with pytest.raises(SourceError, match=r"XDEAD: the source could not be reached"):
        TiingoSource().fetch("XDEAD", JAN, DEC)


def test_a_spent_hourly_allocation_stops_the_batch_and_charges_nothing_further(monkeypatch, tmp_path, capsys):
    import io
    import urllib.error
    import urllib.request

    from occams.ingest import main as ingest_main

    monkeypatch.setenv("TIINGO_API_KEY", "placeholder-value")
    calls = []

    def over(req, timeout):
        calls.append(req.full_url)
        raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {},
                                     io.BytesIO(b'{"detail": "Error: You have run over your hourly request allocation."}'))

    monkeypatch.setattr(urllib.request, "urlopen", over)
    with pytest.raises(RateLimited):
        TiingoSource().fetch("XAAA", JAN, DEC)
    rc = ingest_main(["XAAA", "XBBB", "XCCC", "--start", "2024-01-01", "--end", "2024-12-31", "--archive", str(tmp_path / "a")])
    out = capsys.readouterr().out
    assert rc == 1 and len(calls) == 2 and "XAAA: REFUSED" in out and "STOPPED" in out and "2 not requested: XBBB XCCC" in out
    assert SymbolBudget(tmp_path / "a" / "symbol-budget.json", limit=500).used(__import__("datetime").date.today().strftime("%Y-%m")) == ["XAAA"]


def test_the_live_source_is_never_imported_with_a_token_in_code():
    src = (Path(__file__).resolve().parent.parent / "occams" / "data" / "source.py").read_text()
    assert "Token " in src and 'os.environ.get("TIINGO_API_KEY")' in src
    assert "TIINGO_API_KEY=" not in src


# ---- M4.8: the archive --------------------------------------------------

def test_reproduction_reads_the_archive_and_a_vendor_change_cannot_alter_it(tmp_path):
    arch = BarArchive(tmp_path / "a")
    src = FixtureSource(FIXTURE)
    first = ingest(src, "YSYN", JAN, DEC, archive=arch, budget=None, month="2026-09")
    # the vendor revises a print
    revised = json.loads(FIXTURE.read_text())
    revised["YSYN"][10]["close"] = revised["YSYN"][10]["close"] + 1.0
    p = tmp_path / "revised.json"
    p.write_text(json.dumps(revised))
    second = ingest(FixtureSource(p), "YSYN", JAN, DEC, archive=arch, budget=None, month="2026-09")
    assert second.sha != first.sha
    bars, _ = arch.get(first.sha)
    assert bars.close[10] == first.bars.close[10]  # the original series is intact beside the revision
    assert len(arch.entries()) == 2


def test_the_archive_is_content_addressed_and_immutable(tmp_path):
    arch = BarArchive(tmp_path / "a")
    got = ingest(FixtureSource(FIXTURE), "YSYN", JAN, DEC, archive=arch, budget=None, month="2026-09")
    again = arch.put(got.bars, got.actions, source_id="synthetic")
    assert again == got.sha and len([p for p in (tmp_path / "a" / "bars").iterdir()]) == 1  # one file; the manifest notes both puts
    path = tmp_path / "a" / "bars" / f"{got.sha}.json"
    path.write_text(path.read_text().replace("YSYN", "YSYM", 1))
    with pytest.raises(RuntimeError, match="corruption"):
        arch.get(got.sha)
    with pytest.raises(NotArchived):
        arch.get("0" * 64)


# ---- M4.9: rights, S9 ---------------------------------------------------

@pytest.mark.parametrize("use,tiingo_ok", [
    (Use.PRIVATE_RETENTION, True),
    (Use.INTERNAL_REPRODUCTION, True),
    (Use.RAW_REDISTRIBUTION, False),
    (Use.DERIVED_ARTIFACTS, False),      # unanswered in the terms -> refused until answered
    (Use.SYNTHETIC_PUBLICATION, True),
])
def test_s9_each_use_is_independently_allowed_or_refused(use, tiingo_ok):
    if tiingo_ok:
        assert require("tiingo-starter", use).source_id == "tiingo-starter"
    else:
        with pytest.raises(RightsRefused):
            require("tiingo-starter", use)
    assert require("synthetic", use).source_id == "synthetic"


def test_unanswered_is_a_refusal_that_says_to_ask():
    with pytest.raises(RightsRefused, match="ask the vendor in writing"):
        require("tiingo-starter", Use.DERIVED_ARTIFACTS)


def test_the_tiingo_record_carries_the_dated_delisted_coverage_observation():
    from occams.data.rights import TIINGO_STARTER
    n = TIINGO_STARTER.notes
    assert "2026-09-12" in n and "M12.1b" in n and "FRC" in n and "BBBY" in n and "SHLD" in n and "survivorship" in n
    assert Rights("x", "2026-09-10", "p", {u: Answer.ALLOWED for u in Use}).notes == ""


def test_a_rights_record_must_answer_every_use():
    with pytest.raises(ValueError, match="unrecorded"):
        Rights("x", "2026-09-10", "p", {Use.PRIVATE_RETENTION: Answer.ALLOWED})


def test_export_enforces_rights_at_the_boundary():
    rows = FixtureSource(FIXTURE).fetch("YSYN", JAN, DEC)
    bars, _ = parse_tiingo("YSYN", rows)
    assert export(bars, source_id="tiingo-starter", use=Use.INTERNAL_REPRODUCTION) is bars
    with pytest.raises(RightsRefused):
        export(bars, source_id="tiingo-starter", use=Use.RAW_REDISTRIBUTION)


def test_the_archive_refuses_a_source_that_may_not_retain(tmp_path):
    reg = dict(REGISTRY)
    reg["no-keep"] = Rights("no-keep", "2026-09-10", "expiry: delete at end of subscription",
                            {u: Answer.FORBIDDEN for u in Use})
    from occams.data import rights as rmod
    import occams.data.archive as amod
    rows = FixtureSource(FIXTURE).fetch("YSYN", JAN, DEC)
    bars, acts = parse_tiingo("YSYN", rows)
    old = rmod.REGISTRY.copy()
    try:
        rmod.REGISTRY["no-keep"] = reg["no-keep"]
        with pytest.raises(RightsRefused):
            amod.BarArchive(tmp_path / "a").put(bars, acts, source_id="no-keep")
    finally:
        rmod.REGISTRY.clear()
        rmod.REGISTRY.update(old)
    assert reg["no-keep"].time_bounded()
    assert os.environ.get("TIINGO_API_KEY") is None or True
