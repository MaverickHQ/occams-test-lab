"""M12.1 — universes as records, each with its own frozen calendar."""

from __future__ import annotations

from occams.calendar import main as calendar_main
from occams.data.partitions import Partitions, declared_universe, freeze_calendar, frozen_calendar, span_for
from occams.register import Register
from occams.universe import main as universe_main
from occams.whatif import universes
from tests.test_calendar import LO, latest
from tests.test_console import config_on_disk
from tests.test_programme2 import archive


def declare(reg_path, name="etfs", members="AAA,BBB,CCC", extra=()):
    return universe_main(["declare", "--register", str(reg_path), "--name", name, "--members", members,
                          "--rule", "the fixture's three names", "--bias", "none: synthetic", "--chosen-on", "2026-09-12", *extra])


def test_a_universe_is_a_record_with_its_rule_and_its_bias_and_is_never_edited(tmp_path):
    reg = tmp_path / "p2.jsonl"
    assert universe_main(["show", "--register", str(reg)]) == 1
    assert declare(reg) == 0
    u = declared_universe(Register(reg), "etfs")
    assert u["members"] == ["AAA", "BBB", "CCC"] and u["rule"] and u["bias"] and u["source_id"] == "tiingo-starter"
    assert declare(reg) == 1                                   # the same name again is refused
    assert declare(reg, members="AAA,BBB") == 1                # fewer than three names is refused
    assert declare(reg, name="etfs", members="AAA,BBB,CCC,DDD", extra=("--notes", "supersedes the first etfs record: DDD listed")) == 0
    assert universe_main(["show", "--register", str(reg), "--name", "etfs"]) == 0
    assert universe_main(["declare", "--register", str(reg), "--name", "x", "--members", "A,B,C", "--rule", "r", "--bias", "b",
                          "--chosen-on", "2026-09-12", "--source", "nowhere"]) == 1   # no rights record


def test_a_member_the_archive_does_not_hold_is_refused_when_the_archive_is_given(tmp_path):
    archive(tmp_path / "archive")
    reg = tmp_path / "p2.jsonl"
    assert declare(reg, members="AAA,BBB,ZZZ", extra=("--archive", str(tmp_path / "archive"))) == 1
    assert declare(reg, extra=("--archive", str(tmp_path / "archive"))) == 0


def test_each_universe_has_its_own_frozen_calendar(tmp_path):
    a = archive(tmp_path / "archive")
    reg = Register(tmp_path / "p2.jsonl")
    split = Partitions(0.3, 0.5, 0.2)
    two = {n: b for n, b in latest(a).items() if n != "CCC"}
    c_all = freeze_calendar(reg, latest(a), split=split, config_sha="cfg", reason="all", universe="all")
    c_two = freeze_calendar(reg, two, split=split, config_sha="cfg", reason="two", universe="two", end=LO + 999)
    assert c_all["universe"] == "all" and c_two["universe"] == "two" and c_two["end_day"] == LO + 999
    assert span_for(reg, latest(a), split, universe="all") == (LO, LO + 1199)
    assert span_for(reg, two, split, universe="two") == (LO, LO + 999)
    assert frozen_calendar(reg) is None and frozen_calendar(reg, "two")["end_day"] == LO + 999   # the Register-wide calendar is separate


def test_the_calendar_command_freezes_a_declared_universe_and_refuses_an_undeclared_one(tmp_path):
    archive(tmp_path / "archive")
    config_on_disk(tmp_path)
    reg = tmp_path / "p2.jsonl"
    common = ["--archive", str(tmp_path / "archive"), "--register", str(reg), "--config", str(tmp_path / "occams.toml")]
    assert calendar_main(["freeze", *common, "--universe", "etfs", "--reason", "first"]) == 1     # not declared
    assert declare(reg) == 0
    assert calendar_main(["freeze", *common, "--universe", "etfs", "--reason", "first"]) == 0
    assert calendar_main(["show", "--register", str(reg), "--universe", "etfs"]) == 0
    assert calendar_main(["show", "--register", str(reg), "--universe", "nope"]) == 1
    assert frozen_calendar(Register(reg), "etfs")["names"] == ["AAA", "BBB", "CCC"]


def test_whatif_reads_declared_universes(tmp_path):
    cfg = config_on_disk(tmp_path)
    a = archive(tmp_path / "archive")
    reg = tmp_path / "p2.jsonl"
    declare(reg, name="two", members="AAA,BBB")
    declare(reg, name="three", members="AAA,BBB,CCC")
    us = universes(cfg, a, Register(reg))
    assert [u["name"] for u in us] == ["archive: AAA, BBB, CCC", "three"] and us[1]["names"] == 3
    # a superseding record under the same name (ADR-0042) is one universe, one row — the latest record's members
    declare(reg, name="three", members="AAA,BBB,CCC", extra=("--notes", "supersedes the first record: a flat bar named"))
    us = universes(cfg, a, Register(reg))
    assert [u["name"] for u in us] == ["archive: AAA, BBB, CCC", "three"] and us[1]["names"] == 3
    # a declared universe is measured on its own frozen calendar, not the archive's span
    freeze_calendar(Register(reg), {n: b for n, b in latest(a).items()}, split=Partitions.from_config(cfg), config_sha="c",
                    reason="short", universe="three", end=LO + 599)
    us = universes(cfg, a, Register(reg))
    assert us[1]["measurement_days"] == Partitions.from_config(cfg).bounds_over(LO, LO + 599)["measurement"][1] - \
        Partitions.from_config(cfg).bounds_over(LO, LO + 599)["measurement"][0] and us[0]["measurement_days"] > us[1]["measurement_days"]
