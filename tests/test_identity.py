"""M16.10 (ADR-0055; the review's F13) — the engine is identified by what it imports, only
code can make the tree dirty, and dirty or unknown code does not measure.

The suite itself runs on a tree whose identity is supplied to it (``tests/conftest.py``),
so a change under development does not refuse its own tests; the tests here take the real
identity back where they need it."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

from occams.question import measure_question, resolve_question
from tests.test_question import _registered, lab  # noqa: F401 — `lab` is the fixture `_registered` takes

ROOT = Path(__file__).resolve().parents[1]


def _copy_of_the_code(tmp_path: Path) -> Path:
    shutil.copytree(ROOT / "occams", tmp_path / "occams", ignore=shutil.ignore_patterns("__pycache__"))
    return tmp_path


def test_code_closure_sha_covers_fills(tmp_path):
    """One byte of the vendored fill model changes the hash; the hand-kept list of eleven
    files it replaces left the fill model, the sizing rule, the measurement contract and the
    guards out. A page template changes nothing: it is not something a measurement imports."""
    from occams import identity

    root = _copy_of_the_code(tmp_path)
    before = identity.code_closure_sha(root=root)
    assert before == identity.code_closure_sha() and len(before) == 16
    files = identity.closure(root=root)
    for rel in ("occams/core/execution.py", "occams/sizing.py", "occams/measurement.py", "occams/guards/beats_null.py",
                "occams/guards/forward.py", "occams/data/partitions.py", "occams/engine/probes.py", "occams/inference.py",
                "occams/loop.py", "occams/survey/run.py", "occams/__init__.py"):
        assert rel in files, rel
    # a command line's imports are not a measurement's; names are matched exactly, so the closure is the same on any file system
    assert not [f for f in files if f.startswith("occams/console/")] and "occams/survey/page.py" not in files
    assert len({f.lower() for f in files}) == len(files) and "occams/register/Store.py" not in files
    fills = root / "occams" / "core" / "execution.py"
    fills.write_bytes(fills.read_bytes() + b"#")
    assert identity.code_closure_sha(root=root) != before
    fills.write_bytes(fills.read_bytes()[:-1])
    page = root / "occams" / "console" / "render.py"
    page.write_bytes(page.read_bytes() + b"#")
    assert identity.code_closure_sha(root=root) == before


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", "-c", "commit.gpgsign=false", *args],
                          cwd=root, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def repo(tmp_path):
    (tmp_path / "occams").mkdir()
    (tmp_path / "occams" / "x.py").write_text("X = 1\n")
    (tmp_path / "register").mkdir()
    (tmp_path / "register" / "x.jsonl").write_text("{}\n")
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 't'\n")
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-q", "-m", "c")
    return tmp_path


@pytest.mark.real_identity
def test_register_append_does_not_dirty_engine(repo):
    """Every programme 2 verdict reads `-dirty` because the loop's own Register writes dirtied
    the tree. Only code can: a Register, an archive or a page written during a run cannot."""
    from occams import identity

    head = _git(repo, "rev-parse", "HEAD")
    assert identity.engine_sha(root=repo) == head and identity.dirty_paths(root=repo) == ()
    with (repo / "register" / "x.jsonl").open("a") as f:
        f.write("{}\n")
    (repo / "docs").mkdir()
    (repo / "docs" / "page.html").write_text("<p>built</p>")
    assert identity.engine_sha(root=repo) == head                       # the stores and the pages are outputs
    (repo / "occams" / "x.py").write_text("X = 2\n")
    assert identity.engine_sha(root=repo) == head + "-dirty" and identity.dirty_paths(root=repo) == ("occams/x.py",)
    with pytest.raises(identity.EngineNotClean, match="occams/x.py"):
        identity.require_clean("a measurement", root=repo)


@pytest.mark.real_identity
def test_a_tree_with_no_commit_is_unknown_and_refused(tmp_path):
    from occams import identity

    (tmp_path / "occams").mkdir()
    assert identity.commit(root=tmp_path) == "unknown" and identity.engine_sha(root=tmp_path) == "unknown"
    with pytest.raises(identity.EngineNotClean, match="cannot be read"):
        identity.require_clean("a measurement", root=tmp_path)


def test_measure_refuses_dirty_code(lab, tmp_path, monkeypatch):  # noqa: F811
    """REGISTERED -> MEASURED on code that is not what any commit holds is refused by name,
    before the engine runs and before anything is appended."""
    from occams import identity

    c, reg, budget, arch, q = _registered(lab, tmp_path, drift=0.0, edge=True)
    n = len(reg.records())
    monkeypatch.setattr(identity, "dirty_paths", lambda root=identity.ROOT: ("occams/engine/day_boxed.py",))
    with pytest.raises(identity.EngineNotClean, match="occams/engine/day_boxed.py"):
        measure_question(q, cfg=c, archive=arch, register=reg, seed=3, null_draws=400)
    assert len(reg.records()) == n


def test_measure_refuses_unknown_commit(lab, tmp_path, monkeypatch):  # noqa: F811
    from occams import identity

    c, reg, budget, arch, q = _registered(lab, tmp_path, drift=0.0, edge=True)
    n = len(reg.records())
    monkeypatch.setattr(identity, "commit", lambda root=identity.ROOT: "unknown")
    with pytest.raises(identity.EngineNotClean, match="cannot be read"):
        measure_question(q, cfg=c, archive=arch, register=reg, seed=3, null_draws=400)
    assert len(reg.records()) == n


@pytest.mark.slow
def test_a_survey_refuses_dirty_code(tmp_path, monkeypatch):
    from occams import identity
    from occams.survey.run import run_survey
    from tests.test_survey_run import world

    a, cfg, reg, grid = world(tmp_path)
    n = len(reg.records())
    monkeypatch.setattr(identity, "dirty_paths", lambda root=identity.ROOT: ("tools/x.py",))
    with pytest.raises(identity.EngineNotClean, match="tools/x.py"):
        run_survey(grid, archive=a, register=reg, cfg=cfg, out=tmp_path / "out", seed=7, workers=1, log=lambda *_: None)
    assert len(reg.records()) == n and not (tmp_path / "out" / "cells").exists()


def test_measured_and_resolved_records_carry_the_content_hash(lab, tmp_path):  # noqa: F811
    from occams import identity

    c, reg, budget, arch, q = _registered(lab, tmp_path, drift=0.0, edge=True)
    q, m = measure_question(q, cfg=c, archive=arch, register=reg, seed=3, null_draws=400)
    q, v, _ = resolve_question(q, m, register=reg, archive=arch, seed=3, path_draws=50)
    now = identity.code_closure_sha()
    stamped = [r for r in reg.records() if r["type"] in ("HypothesisMeasured", "HypothesisResolved")]
    assert len(stamped) == 2 and all(r["engine_code_sha"] == now for r in stamped) and m.engine_code_sha == v.engine_code_sha == now
    assert all("-dirty" not in r["engine_sha"] and r["engine_sha"] != "unknown" for r in stamped)


@pytest.mark.real_identity
def test_the_controls_are_exempt_and_say_so(tmp_path, capsys, monkeypatch):
    """The apparatus controls run on whatever tree `make check` finds — that is what makes
    them a check of a change before it is committed — and they print the identity they ran on."""
    from occams import controls, identity

    monkeypatch.setattr(identity, "dirty_paths", lambda root=identity.ROOT: ("occams/engine/day_boxed.py",))
    assert controls.main(["null"]) == 0
    out = capsys.readouterr().out
    assert "exempt from the clean-code rule (ADR-0055)" in out and identity.code_closure_sha() in out and "-dirty" in out


def test_the_vendored_core_is_untouched_and_no_longer_asked_for_the_engine_sha():
    """ADR-0055: `core/archive.py` stays byte-identical (`make provenance` says so); the lab
    stops calling its `engine_sha` and asks `occams.identity` instead."""
    for path in sorted((ROOT / "occams").rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        if rel.startswith("occams/core/") or rel == "occams/identity.py":
            continue
        assert "core.archive import engine_sha" not in path.read_text(encoding="utf-8"), rel
