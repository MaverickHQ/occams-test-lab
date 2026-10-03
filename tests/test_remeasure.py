"""M15.9 — a resolved question re-measured on a rolling cut of its own measurement partition: each roll a record
in a rolls Register beside the programme's, the programme's Register untouched, the reserve never read."""

from __future__ import annotations

import pytest

from occams.guards import Refused
from occams.loop import run
from occams.question import measurement_world
from occams.register import Register
from occams.rolls import main as remeasure_main, windows
from tests.test_loop import cfg, queued


def test_windows_start_later_and_end_where_the_partition_ends():
    assert windows((100, 400), 2) == [(200, 400), (300, 400)]
    assert windows((100, 400), 1) == [(250, 400)]


@pytest.mark.slow
def test_a_roll_is_a_record_beside_the_programme_never_in_it_and_never_beyond_the_partition(tmp_path, capsys):
    c = cfg(falsifier_count=10)
    reg, arch, queue = queued(tmp_path, c, ["Q-1"], drift=0.0, edge=True)
    res = run(c, register=reg, archive=arch, queue=queue, seed=5, null_draws=300, path_draws=50)
    assert [o for _, o in res.resolved] == ["supported"]
    n_before = len(reg.records())
    (q,) = [x for x in queue.questions() if x.id == "Q-1"]
    bounds = measurement_world(q, cfg=c, archive=arch, register=reg)["bounds"]
    with pytest.raises(Refused, match="reserve is never read"):
        measurement_world(q, cfg=c, archive=arch, register=reg, window=(bounds[0], bounds[1] + 10))
    import copy

    from tests.test_config import FIXTURE
    from tests.test_console import _toml
    from tests.test_whatif import AFFORDABLE_AXES

    raw = copy.deepcopy(FIXTURE)                                  # the loop test's config, on disk (tests/test_loop.py cfg())
    raw["capital"]["currency"] = "USD"
    raw["alpha"]["axes"] = copy.deepcopy(AFFORDABLE_AXES)
    raw["alpha"]["axes"]["regime"]["budget"] = 0.6
    raw["alpha"]["axes"]["price_daily"]["budget"] = 0.15
    raw["lab"] = {"falsifier_count": 10, "falsifier_outcome": "null", "overlap_threshold": 0.9}
    cfg_path = tmp_path / "c.toml"
    cfg_path.write_text(_toml(raw), encoding="utf-8")
    common = ["--question", "Q-1", "--register", str(tmp_path / "r.jsonl"), "--queue", str(tmp_path / "q.jsonl"), "--archive", str(tmp_path / "archive"),
              "--config", str(cfg_path), "--seed", "5", "--rolls", "2", "--null-draws", "200"]
    assert remeasure_main([*common, "--out", str(tmp_path / "r.jsonl")]) == 1          # never the programme's Register
    assert "never in it" in capsys.readouterr().out
    assert remeasure_main([*common, "--out", str(tmp_path / "rolls.jsonl")]) == 0
    out = capsys.readouterr().out
    assert "roll 1/2" in out and "roll 2/2" in out and "a roll is not a verdict" in out
    rolls = Register(tmp_path / "rolls.jsonl").records()
    assert [r["type"] for r in rolls] == ["RollMeasured", "RollMeasured"] and [r["roll"] for r in rolls] == [1, 2]
    assert all(bounds[0] < r["window_start_day"] < r["window_end_day"] == bounds[1] for r in rolls)
    assert rolls[0]["window_start_day"] < rolls[1]["window_start_day"] and all(r["n"] > 0 for r in rolls)
    assert all(isinstance(r["powered"], bool) and r["powered"] == (r["n"] >= q.hypothesis.required_n) for r in rolls)
    assert all(r["source_register"] == "r.jsonl" and r["source_head"] == reg.chain()[-1]["sha"] for r in rolls)
    assert len(reg.records()) == n_before                                              # the programme's Register untouched
