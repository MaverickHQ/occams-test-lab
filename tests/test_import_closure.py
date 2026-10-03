"""M1.3 — ``occams/core/`` imports nothing outside itself, the standard
library, numpy and pandas. The rule lives in ``tools/closure.py`` so the
quickstart shows the same check CI enforces."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _closure():
    spec = importlib.util.spec_from_file_location("_closure", ROOT / "tools" / "closure.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_core_is_import_closed():
    assert _closure().leaks() == []


def test_the_admitted_lazy_import_is_the_only_one():
    assert {("archive", "boto3")} == _closure().LAZY_ADMITTED


def test_core_has_twelve_modules_and_not_report():
    mods = sorted(p.stem for p in (ROOT / "occams" / "core").glob("*.py") if p.stem != "__init__")
    assert len(mods) == 12 and "execution" in mods and "report" not in mods
