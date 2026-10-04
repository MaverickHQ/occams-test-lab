"""M16.17 (ADR-0055 §5; the review's F14) — a stamped source is addressable without the history.

The Registers stamp commits this repository does not hold. `SOURCES.toml` names each by its
tree, by the content hash of the code a measurement imports there, and by the digest of an
archive of the tree; the snapshots live in the private archive and are never committed; and a
reproduction can run from one — or fail loudly when it is not there, never skip."""

from __future__ import annotations

import gzip
import json
import subprocess
from pathlib import Path

import pytest

from occams import sources

ROOT = Path(__file__).resolve().parents[1]


def test_every_resolved_names_a_known_source():
    """Every commit a measured, a resolved or a surveyed record stamps is in the manifest, whole — and the manifest
    names nothing else."""
    stamped = sources.stamped()
    known = sources.load()
    assert len(stamped) == 7 and set(stamped) == set(known)          # five verdicts' commits and two surveys'
    assert sources.check() == []
    for commit, entry in known.items():
        assert len(commit) == 40 and len(entry["tree"]) == 40 and len(entry["engine_code_sha"]) == 16 and len(entry["tar_sha256"]) == 64
        assert entry["stamped_by"] == stamped[commit]
    resolved = [r for records in stamped.values() for r in records if "HypothesisResolved" in r]
    assert sorted(r.split()[-1] for r in resolved) == ["Q-003", "Q-004", "Q-005", "Q2-001", "Q2-002"]


def test_a_stamped_commit_the_manifest_does_not_name_is_reported(tmp_path):
    manifest = tmp_path / "SOURCES.toml"
    entries = list(sources.load().values())
    manifest.write_text(sources.dump(entries[1:]), encoding="utf-8")
    problems = sources.check(manifest)
    assert len(problems) == 1 and entries[0]["commit"][:12] in problems[0] and "not named" in problems[0]
    manifest.write_text(sources.dump([{**entries[0], "tree": "short"}] + entries[1:]), encoding="utf-8")
    assert any("not whole" in p for p in sources.check(manifest))


def test_no_snapshot_is_committed():
    """The snapshots hold trees the publication scan cleaned; they stay in the private archive."""
    tracked = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    assert not [f for f in tracked if f.startswith("archive/") or f.endswith((".tar.gz", ".tar", ".tgz"))]
    assert "archive/" in (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    assert "SOURCES.toml" in tracked or (ROOT / "SOURCES.toml").exists()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=none", "-c", "commit.gpgsign=false", *args], cwd=root,
                          capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def private(tmp_path):
    """A small repository standing in for the private history: one commit that a Register stamps."""
    root = tmp_path / "repo"
    (root / "occams" / "engine").mkdir(parents=True)
    (root / "occams" / "__init__.py").write_text("")
    (root / "occams" / "engine" / "__init__.py").write_text("")
    (root / "occams" / "engine" / "day_boxed.py").write_text("NAME = 'day_boxed'\n")
    (root / "occams" / "loop.py").write_text("from occams.engine import day_boxed\n")
    (root / "register").mkdir()
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the commit a verdict stamps")
    commit = _git(root, "rev-parse", "HEAD")
    payload = {"type": "HypothesisResolved", "hypothesis_id": "Q-1", "engine_sha": f"{commit}-dirty"}
    line = json.dumps({"seq": 0, "prev": "genesis", "sha": "x", "payload": payload}) + "\n"
    (root / "register" / "r.jsonl").write_text(line)
    return root, commit


def test_a_snapshot_is_built_named_and_extracted_whole(private, tmp_path):
    root, commit = private
    archive, manifest = tmp_path / "archive", tmp_path / "SOURCES.toml"
    (entry,) = sources.build(root=root, archive=archive, registers=("register/r.jsonl",), manifest=manifest)
    assert entry["commit"] == commit and entry["tree"] == _git(root, "rev-parse", "HEAD^{tree}") and entry["stamped_by"] == ["r#0 HypothesisResolved Q-1"]
    assert sources.snapshot_path(archive, commit).exists() and sources.check(manifest, ("register/r.jsonl",), root=root) == []
    again = sources.build(root=root, archive=archive, registers=("register/r.jsonl",), manifest=manifest)
    assert again == [entry]                                                    # the same bytes, the same digests, every time
    tree = sources.extract(commit + "-dirty", archive=archive, dest=tmp_path / "tree", manifest=manifest)
    assert (tree / "occams" / "loop.py").read_text() == "from occams.engine import day_boxed\n" and not (tree / ".git").exists()


def test_a_snapshot_that_is_not_the_named_tree_is_refused(private, tmp_path):
    root, commit = private
    archive, manifest = tmp_path / "archive", tmp_path / "SOURCES.toml"
    sources.build(root=root, archive=archive, registers=("register/r.jsonl",), manifest=manifest)
    path = sources.snapshot_path(archive, commit)
    with path.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:
        gz.write(b"not the tree")
    with pytest.raises(sources.SourceMissing, match="its digest differs"):
        sources.extract(commit, archive=archive, dest=tmp_path / "tree", manifest=manifest)
    with pytest.raises(sources.SourceMissing, match="not named"):
        sources.extract("0" * 40, archive=archive, dest=tmp_path / "tree2", manifest=manifest)


@pytest.mark.slow
def test_reproduction_at_source_fails_loudly_without_the_snapshot(tmp_path, capsys, monkeypatch):
    """`--at-source` where the source cannot be produced: exit 2, the reason named, and the word *skip* only to deny it."""
    from occams.config import load
    from occams.ledger.alpha_budget import AlphaBudget
    from occams.question import QuestionQueue, measure_question, resolve_question
    from occams.register import Register
    from occams.reproduce import main as reproduce_main
    from occams.whatif import config_sha
    from tests.test_question import _registered
    from tests.test_reproduce import config_on_disk

    reg = Register(tmp_path / "r.jsonl")
    cfg_path = config_on_disk(tmp_path)
    c = load(cfg_path)
    c, reg, budget, arch, q = _registered((c, reg, AlphaBudget(c, reg, config_sha=config_sha(c))), tmp_path, drift=0.0, edge=True)
    queue = QuestionQueue(tmp_path / "q.jsonl")
    queue.enqueue(q)
    q, m = measure_question(q, cfg=c, archive=arch, register=reg, seed=3, null_draws=300)
    q, v, _ = resolve_question(q, m, register=reg, archive=arch, seed=3, path_draws=50)
    args = ["private", "--question", "Q-1", "--register", str(reg.path), "--queue", str(queue.path), "--archive", str(tmp_path / "archive"),
            "--config", str(cfg_path), "--null-draws", "300", "--at-source"]
    before = reg.path.read_text()
    assert reproduce_main(args) == 2                                       # the commit this verdict stamps is not a named source
    out = capsys.readouterr().out
    assert "REPRODUCTION FAILED" in out and "is not named in SOURCES.toml" in out
    commit = sources.commit_of(v.engine_sha)
    monkeypatch.setattr(sources, "load", lambda manifest=sources.MANIFEST: {commit: {"commit": commit, "tree": "t" * 40,
                                                                                    "engine_code_sha": "c" * 16, "tar_sha256": "d" * 64}})
    assert reproduce_main(args) == 2                                       # named, and its snapshot is not on this machine
    out = capsys.readouterr().out
    assert "no snapshot of" in out and str(tmp_path / "archive" / "source") in out and "a failure, not a skip" in out
    assert reg.path.read_text() == before
