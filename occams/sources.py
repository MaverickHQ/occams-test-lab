"""Sources addressable without the history (M16.17; ADR-0055 §5; the review's F14).

Every verdict stamps the commit that measured it, and the public repository begins at a
snapshot: those commits are not in it (`docs/PUBLICATION.md`, the amendment of 2026-10-03).
A stamp nobody can resolve attests nothing. So each stamped commit is named in a committed
manifest, ``SOURCES.toml``, by three things that can be checked without the history — its
tree hash, the content hash of the code a measurement imports at that tree
(`occams.identity`), and the digest of an archive of the tree — and a snapshot of the tree
is kept **beside the licensed bars, in the private archive, never in the repository**: those
trees hold what the publication scan removed. A reproduction can then run from a snapshot
instead of a checkout::

    python -m occams sources build --archive archive      # needs the private history; writes the manifest and the snapshots
    python -m occams sources check                         # every stamped commit is named; needs neither
    python -m occams reproduce private … --at-source       # extracts the snapshot, verifies it against the manifest, measures in it
"""

from __future__ import annotations

import gzip
import hashlib
import io
import subprocess
import sys
import tarfile
import tempfile
import tomllib
from pathlib import Path

from occams import identity

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "SOURCES.toml"
REGISTERS = ("register/register.jsonl", "register/programme-2.jsonl", "register/programme-3.jsonl")
STAMPING = ("HypothesisMeasured", "HypothesisResolved")
SNAPSHOTS = "source"          # under the private archive: archive/source/<commit>.tar.gz
HEADER = """# The sources the Registers stamp (M16.17, ADR-0055 §5). Each verdict names the commit that
# measured it; this repository begins at a snapshot and does not hold those commits. Each is
# named here by what can be checked without them: its tree, the content hash of the code a
# measurement imports at that tree (occams/identity.py, as hashed today), and the sha256 of
# `git archive` of the tree. The snapshots themselves are kept beside the licensed bars in
# the private archive and are never committed. Written by `python -m occams sources build`.
"""


class SourceMissing(RuntimeError):
    """A stamped source cannot be produced: no snapshot here, or one that is not the tree the manifest names."""


def commit_of(stamp: str) -> str:
    """The commit a record stamps: ``-dirty`` was the loop's own Register appends (ADR-0055), not a change to the code."""
    return str(stamp).split("-")[0]


def stamped(registers=REGISTERS, *, root: Path = ROOT) -> dict[str, list[str]]:
    """commit -> the records that stamp it, across the committed Registers. Read as files: nothing is appended or verified here."""
    import json

    out: dict[str, list[str]] = {}
    for rel in registers:
        path = Path(root) / rel
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            p = rec["payload"]
            where = f"{path.stem}#{rec['seq']}"
            if p["type"] in STAMPING:
                out.setdefault(commit_of(p["engine_sha"]), []).append(f"{where} {p['type']} {p['hypothesis_id']}")
            elif p["type"] == "SurveyRecorded":
                for engine, stamp in sorted((p.get("engine_shas") or {}).items()):
                    if engine != "engine_code_sha":
                        out.setdefault(commit_of(stamp), []).append(f"{where} SurveyRecorded {p['grid_name']} ({engine})")
    return {c: v for c, v in out.items() if c and c != identity.UNKNOWN}


def _git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=root, capture_output=True, check=True).stdout


def snapshot_path(archive: Path, commit: str) -> Path:
    return Path(archive) / SNAPSHOTS / f"{commit}.tar.gz"


def _closure_of_tar(tar_bytes: bytes) -> str:
    with tempfile.TemporaryDirectory(prefix="occams-source-") as tmp:
        with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar:
            tar.extractall(tmp, filter="data")
        return identity.code_closure_sha(root=Path(tmp))


def build(*, root: Path = ROOT, archive: Path, registers=REGISTERS, manifest: Path | None = None) -> list[dict]:
    """From the private history: one entry per stamped commit, and its snapshot written under ``archive``."""
    entries = []
    for commit, records in stamped(registers, root=root).items():       # in the order the Registers stamp them
        try:
            tree = _git(root, "rev-parse", f"{commit}^{{tree}}").decode().strip()
            tar_bytes = _git(root, "archive", "--format=tar", commit)
        except subprocess.CalledProcessError:
            raise SourceMissing(f"commit {commit[:12]} is not in this checkout: `sources build` needs the private history, "
                                f"which is never fetched into the published line") from None
        out = snapshot_path(archive, commit)
        out.parent.mkdir(parents=True, exist_ok=True)
        with out.open("wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as gz:     # no timestamp: the same bytes every time
            gz.write(tar_bytes)
        entries.append({"commit": commit, "tree": tree, "engine_code_sha": _closure_of_tar(tar_bytes),
                        "tar_sha256": hashlib.sha256(tar_bytes).hexdigest(), "stamped_by": records})
    (manifest or Path(root) / MANIFEST.name).write_text(dump(entries), encoding="utf-8")
    return entries


def dump(entries: list[dict]) -> str:
    lines = [HEADER]
    for e in entries:
        lines += ["[[source]]", f'commit = "{e["commit"]}"', f'tree = "{e["tree"]}"', f'engine_code_sha = "{e["engine_code_sha"]}"',
                  f'tar_sha256 = "{e["tar_sha256"]}"', "stamped_by = [" + ", ".join(f'"{r}"' for r in e["stamped_by"]) + "]", ""]
    return "\n".join(lines)


def load(manifest: Path = MANIFEST) -> dict[str, dict]:
    if not Path(manifest).exists():
        return {}
    return {e["commit"]: e for e in tomllib.loads(Path(manifest).read_text(encoding="utf-8")).get("source", [])}


def check(manifest: Path = MANIFEST, registers=REGISTERS, *, root: Path = ROOT) -> list[str]:
    """What is wrong, in sentences: a stamped commit the manifest does not name, or an entry that is not whole."""
    known, problems = load(manifest), []
    for commit, records in sorted(stamped(registers, root=root).items()):
        e = known.get(commit)
        if e is None:
            problems.append(f"commit {commit[:12]} is stamped by {records[0]} and is not named in {Path(manifest).name}")
        elif not (len(e.get("tree", "")) == 40 and len(e.get("engine_code_sha", "")) == 16 and len(e.get("tar_sha256", "")) == 64):
            problems.append(f"the entry for {commit[:12]} in {Path(manifest).name} is not whole: it needs a tree, a content hash and a digest")
    return problems


def extract(commit: str, *, archive: Path, dest: Path, manifest: Path = MANIFEST) -> Path:
    """The stamped tree, from its snapshot, verified against the manifest before a line of it runs: the archive's
    digest, then the content hash of the code a measurement imports. Raises ``SourceMissing``, loudly, otherwise."""
    commit = commit_of(commit)
    entry = load(manifest).get(commit)
    if entry is None:
        raise SourceMissing(f"commit {commit[:12]} is not named in {Path(manifest).name}; a stamped source is named there or it is not known")
    path = snapshot_path(archive, commit)
    if not path.exists():
        raise SourceMissing(f"no snapshot of {commit[:12]} at {path}: the snapshots are kept in the private archive, beside the licensed "
                            f"bars, and are not published (ADR-0055). This is a failure, not a skip")
    tar_bytes = gzip.decompress(path.read_bytes())
    if hashlib.sha256(tar_bytes).hexdigest() != entry["tar_sha256"]:
        raise SourceMissing(f"the snapshot at {path} is not the tree {Path(manifest).name} names for {commit[:12]}: its digest differs")
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(tar_bytes)) as tar:
        tar.extractall(dest, filter="data")
    if identity.code_closure_sha(root=dest) != entry["engine_code_sha"]:
        raise SourceMissing(f"the code extracted for {commit[:12]} does not hash to the content hash {Path(manifest).name} names")
    return dest


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="python -m occams sources")
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="from the private history: write the manifest and the snapshots")
    b.add_argument("--archive", required=True, type=Path)
    sub.add_parser("check", help="every commit a Register stamps is named in the manifest")
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    if a.cmd == "build":
        try:
            entries = build(archive=a.archive)
        except SourceMissing as e:
            print(f"REFUSED: {e}")
            return 2
        for e in entries:
            print(f"{e['commit'][:12]} · tree {e['tree'][:12]} · content {e['engine_code_sha']} · {len(e['stamped_by'])} record(s) · "
                  f"snapshot {snapshot_path(a.archive, e['commit'])}")
        print(f"{len(entries)} source(s) named in {MANIFEST.name}; the snapshots are in the private archive and are never committed")
        return 0
    problems = check()
    for p in problems:
        print(f"MISSING: {p}")
    print(f"sources: {len(load())} named in {MANIFEST.name}" + ("" if problems else "; every commit a Register stamps is among them"))
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
