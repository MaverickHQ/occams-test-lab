"""M11.4 — the console renders the Register, offline. What it must and must
not be able to say."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest

from occams.config import load, parse
from occams.console import build, main
from occams.console.facts import AuthorView, gather
from occams.console.render import calendar, estimate_strip, summarise
from occams.data.archive import BarArchive
from occams.data.bars import Bars, random_walk
from occams.engine.day_boxed import NO_ACTIONS
from occams.ledger.alpha_budget import AlphaSpent, ObservationsConsumed
from occams.register import Register, TamperedHistory
from tests.test_config import FIXTURE

T = "t" * 64   # the template's hash
W = "w" * 64   # the winner cell's hash
E = "e" * 40   # an engine sha
REASONS = ("beats-null: random entry under the same geometry does as well",
           "floor: EV per trade in net R is below the declared floor")


def fixture_register(path: Path, *, resolved: bool = True) -> Register:
    reg = Register(path)
    reg.append(Register.ClassifierFrozen("c" * 64, 20, 100, 0.01, "index", "SPY", 727592, 731275,
                                         "1993-01-29T21:00:00+00:00", "2003-02-28T21:00:00+00:00", ("QQQ", "SPY"),
                                         0.974, {"up": 0.51, "down": 0.35, "ranging": 0.14}, 1, "cfg"))
    reg.append(AlphaSpent("Q-1", "regime", "mechanism", 0.01, 4, 0.04, 0.16, "cfg"))
    reg.append(Register.HypothesisRegistered("Q-1", "mechanism", "regime", "breakout continues in the up regime",
                                             "the winner at or below the null's corrected quantile", 0.15, 50.0, 4, 748, 837,
                                             0.04, "author", None, None, "cfg", False))
    reg.append(ObservationsConsumed("Q-1", "regime", "measurement", 731275, 737414, ("QQQ", "SPY")))
    reg.append(Register.HypothesisMeasured("Q-1", T, "day_boxed", E, 1, "measurement", 1391, 4))
    reg.append(Register.StrategyTransitioned(T, "SPECIFIED", "COMPILED", "Q-1"))
    reg.append(Register.StrategyTransitioned(T, "COMPILED", "MEASURED", "Q-1"))
    if resolved:
        reg.append(Register.PathsArchived("Q-1", W, "p" * 64, 2000, 1391))
        reg.append(Register.RefusalRecorded("MEASURED->FORWARD", REASONS[0], {"p_value": 0.971, "alpha": 0.01}, W, "Q-1"))
        reg.append(Register.HypothesisResolved("Q-1", "null", -0.0466, 82.8, W, E, 1, "measurement", REASONS,
                                               "bounded", T, (1, 0)))
        # M12.6: the depth records that follow a verdict
        reg.append(Register.EraDecomposition("Q-1", W, "measurement",
                                             ({"bounds": [731275, 733321], "n": 460, "ev_net": -0.02}, {"bounds": [733321, 735367], "n": 470, "ev_net": -0.06},
                                              {"bounds": [735367, 737414], "n": 461, "ev_net": -0.06}), (-0.06, -0.04, -0.04), 2, {"QQQ": 2}, 1))
        reg.append(Register.Shrinkage("Q-1", "s" * 64, "cell0123456789ab", 38976, 3739, 0.256, 0.239, 1391, -0.0466, -0.01, -0.0366, -0.3026, -0.2756))
    return reg


def calendar_bars(name: str, *, first: int, days: int, seed: int) -> Bars:
    b = random_walk(name, days=days, seed=seed, sigma_daily=0.01)
    return Bars(b.name, b.open, b.high, b.low, b.close, b.volume, tuple(first + i for i in range(b.n)))


def fixture_archive(root: Path) -> BarArchive:
    a = BarArchive(root)
    a.put(calendar_bars("SPY", first=727592, days=400, seed=1), NO_ACTIONS, source_id="synthetic",
          requested_start="1993-01-01", requested_end="1994-04-01")
    a.put(calendar_bars("QQQ", first=727700, days=292, seed=2), NO_ACTIONS, source_id="synthetic")
    return a


def _toml(d: dict, prefix: str = "") -> str:
    """Enough TOML for the fixture: nested dicts become dotted sections."""
    scalars, tables = [], []
    for k, v in d.items():
        if isinstance(v, dict):
            tables.append(_toml(v, f"{prefix}{k}."))
        elif isinstance(v, bool):
            scalars.append(f"{k} = {'true' if v else 'false'}")
        elif isinstance(v, str):
            scalars.append(f'{k} = "{v}"')
        else:
            scalars.append(f"{k} = {v}")
    head = f"[{prefix[:-1]}]\n" if prefix and scalars else ""
    return head + "\n".join(scalars) + ("\n" if scalars else "") + "".join(tables)


MONEY = {"starting": 987654.0, "risk_per_trade": 1234.5, "max_drawdown_per_strategy": 4321.0,
         "max_drawdown_portfolio": 8765.0, "currency": "ZZZ"}   # distinctive, so their absence from a page is checkable


def config_on_disk(tmp_path: Path):
    d = copy.deepcopy(FIXTURE)
    d["capital"].update(MONEY)
    p = tmp_path / "occams.toml"
    p.write_text(_toml(d), encoding="utf-8")
    return load(p)


def author(tmp_path: Path) -> AuthorView:
    return AuthorView.from_config(config_on_disk(tmp_path))


# ---- what the page is made of ------------------------------------------------------

def test_the_page_is_one_self_contained_file_with_no_script_and_no_network(tmp_path):
    fixture_register(tmp_path / "r.jsonl")
    page, facts = build(tmp_path / "r.jsonl", controls="none", generated="2026-09-12T00:00:00+00:00", repo_sha="abc1234")
    assert page.startswith("<!doctype html>") and '<meta charset="utf-8">' in page
    assert "Eras on the measurement partition" in page and "Missed entries" in page and "Shrinkage from screening" in page   # M12.6
    assert "<script" not in page and "http://" not in page and "https://" not in page and "@import" not in page
    assert "Q-1" in page and "breakout continues in the up regime" in page
    assert facts.head == facts.chain[-1]["sha"] and "chain verified" in page


def test_same_inputs_render_identical_bytes(tmp_path):
    fixture_register(tmp_path / "r.jsonl")
    kw = dict(controls="none", generated="2026-09-12T00:00:00+00:00", repo_sha="abc1234")
    assert build(tmp_path / "r.jsonl", **kw)[0] == build(tmp_path / "r.jsonl", **kw)[0]


def test_a_tampered_register_is_a_failure_not_a_report(tmp_path):
    p = tmp_path / "r.jsonl"
    fixture_register(p)
    lines = p.read_text().splitlines()
    lines[2] = lines[2].replace('"alpha_spent":0.04', '"alpha_spent":0.01')
    assert lines[2] != p.read_text().splitlines()[2]
    p.write_text("\n".join(lines) + "\n")
    with pytest.raises(TamperedHistory):
        gather(p, controls="none")
    assert main(["--register", str(p), "--out", str(tmp_path / "c.html"), "--controls", "none"]) == 1
    assert not (tmp_path / "c.html").exists()


# ---- what the page may and may not say ------------------------------------------------

def test_money_cannot_reach_the_page_even_on_the_authors_build(tmp_path):
    """The configuration is reduced to an AuthorView with no field for
    money; the fixture's capital figures must be absent from the page."""
    cfg = config_on_disk(tmp_path)
    assert cfg.capital.starting == MONEY["starting"] and cfg.capital.currency == "ZZZ"
    assert cfg.alpha.total == parse(copy.deepcopy(FIXTURE), Path("fixture")).alpha.total
    view = AuthorView.from_config(cfg)
    assert not hasattr(view, "capital") and "starting" not in view.__dataclass_fields__
    fixture_register(tmp_path / "r.jsonl")
    page, _ = build(tmp_path / "r.jsonl", author=view, controls="none", generated="g", repo_sha="x")
    for token in ("987654", "1234.5", "4321", "8765", "ZZZ"):
        assert token not in page, token
    assert "author's build" in page and f"of {view.falsifier_count}" in page


def test_the_plain_build_shows_spend_but_no_balances_or_falsifier_count(tmp_path):
    fixture_register(tmp_path / "r.jsonl")
    page, _ = build(tmp_path / "r.jsonl", controls="none", generated="g", repo_sha="x")
    assert "Plain build" in page and "0.0400" in page
    assert "of 0.20" not in page and "Alpha by axis" not in page
    assert "is not shown on a plain build" in page


def test_a_resolution_shows_only_because_a_record_exists(tmp_path):
    fixture_register(tmp_path / "r.jsonl", resolved=False)
    page, facts = build(tmp_path / "r.jsonl", controls="none", generated="g", repo_sha="x")
    assert facts.findings[0].state == "measured" and ">Measured<" in page and ">Null<" not in page
    fixture_register(tmp_path / "s.jsonl", resolved=True)
    page, facts = build(tmp_path / "s.jsonl", controls="none", generated="g", repo_sha="x")
    assert facts.findings[0].state == "null" and ">Null<" in page
    assert "p_value 0.971" in page                      # the recorded evidence, beside the reason
    assert "the template measures, the winner trades" in page
    assert facts.falsifier_standing() == 1


def test_the_estimate_strip_places_every_label_on_one_scale():
    svg = estimate_strip(-0.0466, 0.15)
    assert svg.count("<svg") == 1 and "floor +0.15" in svg and "-0.047 net R" in svg and ">0<" in svg
    wide = estimate_strip(0.9, 0.15)                     # an estimate beyond the default range widens the scale
    assert "+0.95" in wide


# ---- the archive: manifest only, one calendar ------------------------------------------

def test_the_archive_section_reads_the_manifest_and_never_the_bars(tmp_path):
    fixture_register(tmp_path / "r.jsonl")
    a = fixture_archive(tmp_path / "archive")
    page, facts = build(tmp_path / "r.jsonl", archive=tmp_path / "archive", controls="none", generated="g", repo_sha="x")
    assert [s.name for s in facts.series] == ["QQQ", "SPY"] and facts.archive_present
    assert "1993-01-01 to 1994-04-01" in page            # the requested span beside the returned one
    sha = a.entries()[0]["sha"]
    assert sha[:12] in page and "100.0" not in page.split("The Register")[0]   # a content hash, not a price


def test_the_calendar_draws_bands_from_the_register_when_no_config_is_given(tmp_path):
    fixture_register(tmp_path / "r.jsonl")
    fixture_archive(tmp_path / "archive")
    _, facts = build(tmp_path / "r.jsonl", archive=tmp_path / "archive", controls="none", generated="g", repo_sha="x")
    bands = facts.bands()
    assert bands["definition"] == (727592, 731275) and bands["measurement"] == (731275, 737414)
    svg = calendar(facts.series, bands)
    assert ">definition<" in svg and ">SPY<" in svg and ">QQQ<" in svg and "1993" in svg


def test_the_calendar_uses_the_authors_split_over_the_common_span_when_given(tmp_path):
    fixture_register(tmp_path / "r.jsonl")
    fixture_archive(tmp_path / "archive")
    _, facts = build(tmp_path / "r.jsonl", archive=tmp_path / "archive", author=author(tmp_path), controls="none", generated="g", repo_sha="x")
    b = facts.bands()
    assert b["definition"][0] == 727592 and b["reserve"][1] == 727592 + 400
    assert b["definition"][1] == b["measurement"][0] and b["measurement"][1] == b["reserve"][0]


def test_a_bar_index_archive_draws_no_calendar(tmp_path):
    fixture_register(tmp_path / "r.jsonl")
    a = BarArchive(tmp_path / "archive")
    a.put(random_walk("OLD", days=50, seed=3, sigma_daily=0.01), NO_ACTIONS, source_id="synthetic")   # days 0..49
    _, facts = build(tmp_path / "r.jsonl", archive=tmp_path / "archive", controls="none", generated="g", repo_sha="x")
    assert facts.series[0].calendar is False and calendar(facts.series, facts.bands()) == ""


# ---- controls run inside the build ------------------------------------------------------

@pytest.mark.slow
def test_the_controls_recompute_inside_the_build_and_gate_the_exit_code(tmp_path):
    fixture_register(tmp_path / "r.jsonl")
    page, facts = build(tmp_path / "r.jsonl", controls="synthetic", generated="g", repo_sha="x")
    assert len(facts.controls) == 2 and facts.controls_ok
    assert ">Refused<" in page and ">Accepted<" in page and "calibrated for this build" in page
    out = tmp_path / "c.html"
    assert main(["--register", str(tmp_path / "r.jsonl"), "--out", str(out), "--controls", "synthetic"]) == 0
    assert out.exists() and "Null control · synthetic" in out.read_text()


def test_every_register_record_type_has_a_summary(tmp_path):
    reg = fixture_register(tmp_path / "r.jsonl")
    reg.append(Register.LabClosed(3, "null", ("Q-1", "Q-2", "Q-3")))
    reg.append(Register.ReserveLook(T, "Q-1"))
    reg.append(Register.ForwardWindowOpened(W, "Q-1", 25, 90, "2026-09-12", "proposal"))
    reg.append(Register.ForwardWindowResolved(W, "Q-1", "pass", "no defect found", 30, 40, ()))
    for p in reg.records():
        s = summarise(p)
        assert s and "{" not in s, p["type"]
    page, facts = build(tmp_path / "r.jsonl", controls="none", generated="g", repo_sha="x")
    assert facts.lab_closed and "The lab closed" in page and facts.strategies_past_measured() == 0


def refused_at_measurement_register(path: Path) -> Register:
    """A question registered, refused at REGISTERED->MEASURED and never resolved: alpha spent, no verdict (Q3-001, 2026-09-20)."""
    reg = Register(path)
    reg.append(Register.ClassifierFrozen("c" * 64, 20, 100, 0.01, "index", "SPY", 727592, 731275,
                                         "1993-01-29T21:00:00+00:00", "2003-02-28T21:00:00+00:00", ("QQQ", "SPY"),
                                         0.974, {"up": 0.51, "down": 0.35, "ranging": 0.14}, 1, "cfg"))
    reg.append(AlphaSpent("Q-1", "regime", "mechanism", 0.01, 4, 0.04, 0.16, "cfg"))
    reg.append(Register.HypothesisRegistered("Q-1", "mechanism", "regime", "a dip inside an uptrend is bought back",
                                             "the winner at or below the null's corrected quantile", 0.15, 50.0, 4, 748, 837,
                                             0.04, "author", None, None, "cfg", False))
    reg.append(Register.RefusalRecorded("REGISTERED->MEASURED", "the winning cell holds fewer trades than the power plan requires",
                                        {"n": 863, "required_n": 1068}, T, "Q-1"))
    return reg


def test_a_question_refused_at_measurement_and_unresolved_is_named_as_such(tmp_path):
    """M14.5: the Register holds the refusal; the page names the state rather than leaving 'Registered' beside it."""
    refused_at_measurement_register(tmp_path / "r.jsonl")
    facts = gather(tmp_path / "r.jsonl", controls="none")
    (fd,) = facts.findings
    assert fd.state == "registered, refused at measurement, unresolved" and fd.measured is None and fd.resolved is None
    page, _ = build(tmp_path / "r.jsonl", controls="none", generated="g", repo_sha="x")
    assert "Refused at measurement · unresolved" in page and "fewer trades than the power plan requires" in page
    # the plain 'Registered' pill is for a question nothing has happened to yet
    fixture_register(tmp_path / "plain.jsonl", resolved=False)
    assert gather(tmp_path / "plain.jsonl", controls="none").findings[0].state == "measured"
