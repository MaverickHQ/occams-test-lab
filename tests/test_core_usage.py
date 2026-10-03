"""M16.12 (the review's F19) — which of the vendored modules the lab uses, pinned.

`occams/core/` is the donor's code at a recorded hash and is never edited here. The lab
imports three of its modules by name and reaches five more through them; four are carried
and never reached. A change to either set is a recorded decision, and this test is where
it is recorded. And nothing `make check` runs loads the cloud SDK the vendored archive
module can reach for."""

from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path

from occams import identity

ROOT = Path(__file__).resolve().parents[1]
IMPORTED_BY_NAME = {"execution", "power", "stats"}                                  # the fills, the power arithmetic, the block length
REACHED = IMPORTED_BY_NAME | {"archive", "audit", "charset", "privacy", "result"}   # the four the review missed, and `archive` behind `audit`
CARRIED_UNUSED = {"backfill", "calibration", "estimators", "experiment"}            # vendored with their tests; no lab module reaches them


def _core_imports(path: Path) -> set[str]:
    out: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module == "occams.core":
                out.update(a.name for a in node.names)
            elif node.module.startswith("occams.core."):
                out.add(node.module.split(".")[2])
        elif isinstance(node, ast.Import):
            out.update(a.name.split(".")[2] for a in node.names if a.name.startswith("occams.core."))
    return out


def test_the_lab_imports_exactly_these_vendored_modules():
    by_name: dict[str, set[str]] = {}
    for base in ("occams", "scripts", "tools"):
        for path in sorted((ROOT / base).rglob("*.py")):
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith("occams/core/"):
                continue
            for module in _core_imports(path):
                by_name.setdefault(module, set()).add(rel)
    assert set(by_name) == IMPORTED_BY_NAME, by_name
    lab = [f"occams.{p.relative_to(ROOT / 'occams').with_suffix('').as_posix().replace('/', '.')}"
           for p in sorted((ROOT / "occams").rglob("*.py")) if "core" not in p.relative_to(ROOT / "occams").parts[:1] and p.name != "__init__.py"]
    reached = {Path(f).stem for f in identity.closure(lab) if f.startswith("occams/core/")} - {"__init__"}
    assert reached == REACHED, reached
    every = {p.stem for p in (ROOT / "occams" / "core").glob("*.py")} - {"__init__"}
    assert every == REACHED | CARRIED_UNUSED and not REACHED & CARRIED_UNUSED


def test_check_never_imports_boto3():
    """Every lab module imported and both controls run on both engines, in a fresh interpreter:
    the cloud SDK is not a declared dependency, and nothing `make check` does may load it."""
    script = (
        "import importlib, pkgutil, sys, tempfile\n"
        "from pathlib import Path\n"
        "import occams\n"
        "for m in pkgutil.walk_packages(occams.__path__, 'occams.'):\n"
        "    if m.name != 'occams.__main__':\n"
        "        importlib.import_module(m.name)\n"
        "from occams import controls\n"
        "for kind in ('null', 'signal'):\n"
        "    for engine in ('synthetic', 'day_boxed'):\n"
        "        controls.run(kind, controls.load_controls(), Path(tempfile.mkdtemp()), engine=engine)\n"
        "print('boto3' in sys.modules, 'botocore' in sys.modules)\n")
    out = subprocess.run([sys.executable, "-c", script], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    assert out[-2:] == ["False", "False"], out
