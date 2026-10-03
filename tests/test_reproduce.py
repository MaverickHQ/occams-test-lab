"""M11.5 / M11.6 — reproduction fails loudly and never skips (F14, S6). The
private path recreates a stamped Verdict from the archive and fails without
it; the public path proves the pipeline on synthetic fixtures and refuses an
exact-historical claim the rights do not permit."""

from __future__ import annotations

import pytest
import copy
import shutil
from pathlib import Path

from occams.config import load
from occams.ledger.alpha_budget import AlphaBudget
from occams.question import QuestionQueue, measure_question, resolve_question
from occams.register import Register
from occams.reproduce import main as reproduce_main
from occams.whatif import config_sha
from tests.test_config import FIXTURE
from tests.test_console import _toml
from tests.test_question import _registered
from tests.test_whatif import AFFORDABLE_AXES


def config_on_disk(tmp_path: Path) -> Path:
    """The question test's configuration, written down: a reproduction runs under the config the verdict was stamped with."""
    raw = copy.deepcopy(FIXTURE)
    raw["capital"]["currency"] = "USD"
    raw["alpha"]["axes"] = copy.deepcopy(AFFORDABLE_AXES)
    raw["lab"]["overlap_threshold"] = 0.9
    p = tmp_path / "occams.toml"
    p.write_text(_toml(raw), encoding="utf-8")
    return p


@pytest.mark.slow
def test_private_reproduction_recreates_the_stamped_verdict_and_fails_loudly_without_the_archive(tmp_path, capsys):
    reg = Register(tmp_path / "r.jsonl")
    cfg_path = config_on_disk(tmp_path)
    c = load(cfg_path)
    c, reg, budget, arch, q = _registered((c, reg, AlphaBudget(c, reg, config_sha=config_sha(c))), tmp_path, drift=0.0, edge=True)
    queue = QuestionQueue(tmp_path / "q.jsonl")
    queue.enqueue(q)                                                       # the registered question, as the loop would hold it
    q, m = measure_question(q, cfg=c, archive=arch, register=reg, seed=3, null_draws=300)
    q, v, _ = resolve_question(q, m, register=reg, archive=arch, seed=3, path_draws=50)
    assert v.outcome == "supported"
    args = ["private", "--question", "Q-1", "--register", str(reg.path), "--queue", str(queue.path), "--archive", str(tmp_path / "archive"),
            "--config", str(cfg_path), "--null-draws", "300"]
    before = reg.path.read_text()
    assert reproduce_main(args) == 0
    out = capsys.readouterr().out
    assert "REPRODUCED: the stamped Verdict of Q-1 is recreated exactly" in out and "ev_net_r" in out and "config" not in out.split("REPRODUCED")[0].lower().replace("--config", "")
    assert reg.path.read_text() == before                                 # a reproduction writes nothing to the Register
    # a question the queue does not hold, then no archive at all: failures with reasons, never a skip
    assert reproduce_main([*args[:2], "Q-9", *args[3:]]) == 2 and "no HypothesisResolved" in capsys.readouterr().out
    shutil.rmtree(tmp_path / "archive")
    assert reproduce_main(args) == 2
    assert "no archive at" in capsys.readouterr().out                    # S6: a failure with its reason, never a skip


@pytest.mark.slow
def test_public_reproduction_runs_on_synthetic_fixtures_and_refuses_an_exact_historical_claim(capsys):
    assert reproduce_main(["public", "--claim-historical"]) == 1
    assert "cannot be made in public" in capsys.readouterr().out
    assert reproduce_main(["public"]) == 0
    out = capsys.readouterr().out
    assert "scope: synthetic" in out and "no exact-historical claim" in out and "no licensed bar read" in out
    assert out.count("as the control requires") == 4
