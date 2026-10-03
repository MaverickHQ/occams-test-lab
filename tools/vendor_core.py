"""Vendor the donor's import-closed core into ``occams/core/`` — M1.3, M1.5.

The donor is ``prop-challenge-lab`` (read-only; never modified here). Twelve
modules come across: the eleven F1 lists, plus ``execution``, which
``estimators`` imports and F1 did not record — recorded in the status log of
2026-09-10 rather than patched around.

"Vendored unchanged" is honoured up to two **mechanical, documented**
transformations that packaging forces and that are applied by this script,
never by hand:

  R1  import paths: ``from occams.X import …`` → ``from occams.core.X import …``
      and ``from occams import X …``     → ``from occams.core import X …``
      for X in the vendored set only.
  R2  repository root: ``ROOT = Path(__file__).resolve().parent.parent``
      → one more ``.parent``, because the files now sit one directory deeper.
  R3  tests only: the qualified names the audit ledger records —
      string literals ``"occams.X.`` → ``"occams.core.X.`` for X in the set —
      because the ledger names functions by their real module path.

Everything else is byte-identical. ``PROVENANCE.md`` and
``occams/core/PROVENANCE.json`` record, per file, the donor sha256 (before
R1/R2) and the vendored sha256 (after). ``tests/test_provenance.py`` asserts
the vendored hashes on every CI run, so a silent local edit fails the build;
``--verify-donor`` re-derives both hashes from the donor when it is present.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DONOR = Path.home() / "prop-challenge-lab"
DONOR_URL = "https://github.com/MaverickHQ/prop-challenge-lab"

# The eleven F1 names, plus execution (estimators -> execution).
MODULES = ["stats", "estimators", "power", "calibration", "result", "archive",
           "audit", "experiment", "backfill", "privacy", "charset", "execution"]

# Their tests, taken whole. NOT taken: test_execution and test_prepublish
# (each imports donor modules outside the set) and test_archive_config (it
# tests the donor's AWS template and repository layout, not the module).
# One case inside test_archive asserts the donor's pyarrow dependency and is
# deselected in pyproject.toml, by name, with the reason beside it.
TESTS = ["test_stats", "test_estimators", "test_power", "test_calibration",
         "test_archive", "test_backfill", "test_experiment_sop", "test_result",
         "test_charset", "test_privacy", "test_block_bootstrap"]

_NAMES = "|".join(MODULES)
R1_A = re.compile(rf"^(\s*)from occams\.({_NAMES}) import ", re.M)
R1_B = re.compile(rf"^(\s*)from occams import ({_NAMES})\b", re.M)
R2 = re.compile(r"^ROOT = Path\(__file__\)\.resolve\(\)\.parent\.parent$", re.M)
R3 = re.compile(rf"(['\"])occams\.({_NAMES})\.")


def transform(src: str, *, is_test: bool) -> str:
    out = R1_A.sub(r"\1from occams.core.\2 import ", src)
    out = R1_B.sub(r"\1from occams.core import \2", out)
    if not is_test:
        out = R2.sub("ROOT = Path(__file__).resolve().parent.parent.parent", out)
    else:
        out = R3.sub(r"\1occams.core.\2.", out)
    return out


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def donor_sha() -> str:
    out = subprocess.run(["git", "rev-parse", "HEAD"], cwd=DONOR,
                         capture_output=True, text=True, check=True).stdout
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=DONOR,
                           capture_output=True, text=True, check=True).stdout
    if dirty.strip():
        sys.exit("donor working tree is dirty; refusing to record provenance")
    return out.strip()


def vendor() -> int:
    if not DONOR.exists():
        sys.exit(f"donor not found at {DONOR}")
    sha = donor_sha()
    rows = []
    for kind, names, src_dir, dst_dir in (
            ("module", MODULES, DONOR / "occams", ROOT / "occams" / "core"),
            ("test", TESTS, DONOR / "tests", ROOT / "tests" / "core")):
        for n in names:
            src = (src_dir / f"{n}.py").read_bytes()
            text = src.decode("utf-8")
            new = transform(text, is_test=(kind == "test")).encode("utf-8")
            (dst_dir / f"{n}.py").write_bytes(new)
            rows.append({"kind": kind, "file": f"{dst_dir.relative_to(ROOT)}/{n}.py",
                         "donor_file": f"{src_dir.relative_to(DONOR)}/{n}.py",
                         "donor_sha256": sha256_bytes(src),
                         "vendored_sha256": sha256_bytes(new),
                         "loc": text.count("\n"),
                         "transformed": new != src})
    (ROOT / "occams" / "core" / "__init__.py").write_text(
        '"""The vendored core (F1). Provenance: PROVENANCE.md; hashes asserted '
        'by tests/test_provenance.py."""\n')
    (ROOT / "tests" / "core" / "__init__.py").write_text("")
    prov = {"donor": DONOR_URL, "donor_commit": sha, "date": date.today().isoformat(),
            "rules": ["R1 import paths occams.X -> occams.core.X for the vendored set",
                      "R2 ROOT = Path(__file__).resolve().parent.parent -> one more .parent",
                      "R3 tests only: string literals 'occams.X.' -> 'occams.core.X.' for the vendored set"],
            "files": rows}
    (ROOT / "occams" / "core" / "PROVENANCE.json").write_text(json.dumps(prov, indent=1) + "\n")
    md = ["# PROVENANCE — the vendored core", "",
          f"Donor: `{DONOR_URL}` at commit `{sha}`, vendored {prov['date']} by",
          "`tools/vendor_core.py`. **Unchanged except two mechanical rules** the script",
          "applies and `occams/core/PROVENANCE.json` records:", "",
          "- **R1** import paths `occams.X` → `occams.core.X`, for the vendored set only.",
          "- **R2** `ROOT = Path(__file__).resolve().parent.parent` gains one `.parent`,",
          "  because the files sit one directory deeper than in the donor.",
          "- **R3** tests only: string literals `'occams.X.'` → `'occams.core.X.'`, because the",
          "  audit ledger names functions by their real module path.", "",
          "Twelve modules, not eleven: `execution` is imported by `estimators` and F1's",
          "closure record omitted it (status log, 2026-09-10). Eleven test files come",
          "across whole. Not taken: `test_execution` and `test_prepublish` (each imports",
          "donor modules outside the set) and `test_archive_config` (it tests the donor's",
          "AWS template and repository layout). One case in `test_archive` asserts the",
          "donor's pyarrow dependency and is deselected by name in `pyproject.toml`.", "",
          "`tests/test_provenance.py` asserts every vendored sha256 below on each CI run.",
          "`python tools/vendor_core.py --verify-donor` re-derives both columns from the",
          "donor when it is present locally.", "",
          "| kind | file | LOC | donor sha256 | vendored sha256 | transformed |",
          "|---|---|---|---|---|---|"]
    for r in rows:
        md.append(f"| {r['kind']} | `{r['file']}` | {r['loc']} | `{r['donor_sha256'][:16]}…` | "
                  f"`{r['vendored_sha256'][:16]}…` | {'yes' if r['transformed'] else 'no'} |")
    md += ["", f"Module LOC total: {sum(r['loc'] for r in rows if r['kind']=='module')}.",
           "Full hashes are in `occams/core/PROVENANCE.json`."]
    (ROOT / "PROVENANCE.md").write_text("\n".join(md) + "\n")
    print(f"vendored {len(MODULES)} modules and {len(TESTS)} tests from {sha[:12]}")
    return 0


def verify(against_donor: bool) -> int:
    prov = json.loads((ROOT / "occams" / "core" / "PROVENANCE.json").read_text())
    bad = 0
    for r in prov["files"]:
        got = sha256_bytes((ROOT / r["file"]).read_bytes())
        if got != r["vendored_sha256"]:
            print(f"MISMATCH vendored: {r['file']}")
            bad += 1
        if against_donor:
            src = (DONOR / r["donor_file"]).read_bytes()
            if sha256_bytes(src) != r["donor_sha256"]:
                print(f"MISMATCH donor: {r['donor_file']} (donor moved since {prov['donor_commit'][:12]})")
                bad += 1
            elif sha256_bytes(transform(src.decode(), is_test=(r["kind"] == "test")).encode()) != r["vendored_sha256"]:
                print(f"MISMATCH transform: {r['file']}")
                bad += 1
    print(f"provenance: {len(prov['files'])} files, {bad} mismatches")
    return 1 if bad else 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--verify-donor", action="store_true")
    a = ap.parse_args()
    sys.exit(verify(a.verify_donor) if (a.verify or a.verify_donor) else vendor())
