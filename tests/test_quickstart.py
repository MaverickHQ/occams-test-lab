"""S2 — the quickstart is the first thing a reader runs, so it must not rot,
must pass its own controls, and must take under ten seconds."""

from __future__ import annotations

import importlib.util
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("_quickstart", ROOT / "scripts" / "quickstart.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_all_four_controls_pass_under_ten_seconds(capsys):
    t0 = time.perf_counter()
    assert _load().main() == 0
    assert time.perf_counter() - t0 < 10.0
    out = capsys.readouterr().out
    for s in ("ALL FOUR PASS", "PROVENANCE", "IMPORT CLOSURE", "NO DEFAULTS", "POWER",
              "touched no market data, no API key, and no network"):
        assert s in out


def test_controls_as_data_agree_with_m0():
    c = _load().controls()
    assert c["provenance_mismatches"] == 0 and c["modules"] == 12
    assert c["leaks"] == []
    assert c["refused"] is True
    assert c["n_required"] == 714  # docs/M0-ANSWERS.md §M0.15, same parameters


def test_it_reaches_for_nothing_it_should_not():
    src = (ROOT / "scripts" / "quickstart.py").read_text()
    for forbidden in ("boto3", "_client", "requests", "urllib", "socket", "data/"):
        assert forbidden not in src, f"quickstart reaches for {forbidden}"
