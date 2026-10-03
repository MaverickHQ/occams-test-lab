"""ADR-0038 — the calendar is frozen: every partition is cut from a
recorded span, never the archive's live one."""

from __future__ import annotations

import pytest

from occams.calendar import main as calendar_main
from occams.console import build
from occams.data.archive import BarArchive
from occams.data.partitions import AlreadyFrozen, CalendarNotFrozen, Partitions, freeze_calendar, frozen_calendar, span_for
from occams.engine.day_boxed import NO_ACTIONS
from occams.ledger.alpha_budget import ObservationsConsumed
from occams.proposers.price import price_template
from occams.proposers.regime import precommit
from occams.register import Register
from occams.spec.spec import EntryKind
from tests.test_console import config_on_disk
from tests.test_price_proposer import calendar_bars, cfg

LO = 727592
SPLIT = Partitions(0.3, 0.5, 0.2)


def archive(root, *, days=1200, extra: dict | None = None) -> BarArchive:
    a = BarArchive(root)
    for i, n in enumerate(("AAA", "BBB", "CCC")):
        a.put(calendar_bars(n, first=LO, days=(extra or {}).get(n, days), seed=30 + i), NO_ACTIONS, source_id="synthetic")
    return a


def latest(a: BarArchive) -> dict:
    return {n: b for n, (b, _a) in a.latest_bars().items()}


def test_a_fresh_register_cuts_from_the_live_span_and_a_freeze_pins_it(tmp_path):
    a = archive(tmp_path / "archive")
    reg = Register(tmp_path / "r.jsonl")
    assert span_for(reg, latest(a), SPLIT) == (LO, LO + 1199)
    c = freeze_calendar(reg, latest(a), split=SPLIT, config_sha="cfg", reason="first")
    assert c["start_day"] == LO and c["end_day"] == LO + 1199 and c["names"] == ["AAA", "BBB", "CCC"]
    assert c["definition_end_day"] == SPLIT.bounds_over(LO, LO + 1199)["definition"][1]
    # the archive grows by a year for one name; the cut does not move, and the new bars fall in no partition
    a.put(calendar_bars("AAA", first=LO, days=1450, seed=30), NO_ACTIONS, source_id="synthetic")
    assert span_for(reg, latest(a), SPLIT) == (LO, LO + 1199)
    reserve, _ = SPLIT.slice(latest(a)["AAA"], "reserve", span=span_for(reg, latest(a), SPLIT))
    assert reserve.day[-1] == LO + 1199 and reserve.n == 240


def test_a_live_cut_is_refused_once_the_archive_has_grown_past_a_recorded_cut(tmp_path):
    a = archive(tmp_path / "archive")
    reg = Register(tmp_path / "r.jsonl")
    b = SPLIT.bounds_over(LO, LO + 1199)["measurement"]
    reg.append(ObservationsConsumed("Q-x", "price_daily", "measurement", b[0], b[1], ("AAA", "BBB", "CCC")))
    assert span_for(reg, latest(a), SPLIT) == (LO, LO + 1199)        # unchanged archive: the live span still reproduces the cut
    a.put(calendar_bars("BBB", first=LO, days=1210, seed=31), NO_ACTIONS, source_id="synthetic")   # ten days later
    with pytest.raises(CalendarNotFrozen, match="calendar freeze"):
        span_for(reg, latest(a), SPLIT)
    with pytest.raises(CalendarNotFrozen):
        precommit(price_template(EntryKind.DOWN_RUN, hold_bars=3, runs=3), archive=a, cfg=cfg(), register=reg, seed=1)


def test_the_freeze_must_reproduce_every_boundary_the_register_already_used(tmp_path):
    a = archive(tmp_path / "archive")
    reg = Register(tmp_path / "r.jsonl")
    b = SPLIT.bounds_over(LO, LO + 1199)["measurement"]
    reg.append(ObservationsConsumed("Q-x", "price_daily", "measurement", b[0], b[1], ("AAA", "BBB", "CCC")))
    a.put(calendar_bars("BBB", first=LO, days=1210, seed=31), NO_ACTIONS, source_id="synthetic")   # ten days later
    with pytest.raises(ValueError, match="an end day in"):
        freeze_calendar(reg, latest(a), split=SPLIT, config_sha="cfg", reason="late")
    c = freeze_calendar(reg, latest(a), split=SPLIT, config_sha="cfg", reason="pinned", end=LO + 1199)
    assert (c["start_day"], c["measurement_end_day"]) == (LO, b[1]) and span_for(reg, latest(a), SPLIT) == (LO, LO + 1199)


def test_a_second_freeze_is_a_recorded_supersession(tmp_path):
    a = archive(tmp_path / "archive")
    reg = Register(tmp_path / "r.jsonl")
    freeze_calendar(reg, latest(a), split=SPLIT, config_sha="cfg", reason="first")
    with pytest.raises(AlreadyFrozen, match="supersedes"):
        freeze_calendar(reg, latest(a), split=SPLIT, config_sha="cfg", reason="again")
    c = freeze_calendar(reg, latest(a), split=SPLIT, config_sha="cfg", reason="a day less", end=LO + 1198,
                        supersedes=f"{LO}-{LO + 1199}")
    assert frozen_calendar(reg)["end_day"] == LO + 1198 and c["supersedes"] == f"{LO}-{LO + 1199}"


def test_the_console_draws_bands_from_the_record_on_a_plain_build(tmp_path):
    a = archive(tmp_path / "archive")
    reg = Register(tmp_path / "r.jsonl")
    freeze_calendar(reg, latest(a), split=SPLIT, config_sha="cfg", reason="first")
    page, facts = build(tmp_path / "r.jsonl", archive=tmp_path / "archive", controls="none", generated="g", repo_sha="x")
    assert facts.bands() == SPLIT.bounds_over(LO, LO + 1199) and ">definition<" in page and "CalendarFrozen" in page


def test_the_command_freezes_and_shows(tmp_path):
    archive(tmp_path / "archive")
    config_on_disk(tmp_path)
    args = ["--archive", str(tmp_path / "archive"), "--register", str(tmp_path / "r.jsonl"), "--config", str(tmp_path / "occams.toml")]
    assert calendar_main(["show", "--register", str(tmp_path / "r.jsonl")]) == 1
    assert calendar_main(["freeze", *args, "--reason", "first"]) == 0
    assert calendar_main(["freeze", *args, "--reason", "twice"]) == 1      # a second freeze without supersedes is refused
    assert calendar_main(["show", "--register", str(tmp_path / "r.jsonl")]) == 0
