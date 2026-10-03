"""M16.3 — the documents say what the code does (the review's F22, and the wording half of F08).

The partitions are cut 30 / 50 / 20, oldest first; "half" was never true of either. The
signal control names five checks since ADR-0043. The controls' comment states the count
the plan computes, not one remembered.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from occams.core.power import n_for_mean_shift

ROOT = Path(__file__).resolve().parent.parent


def test_no_halves():
    for doc in ("README.md", "docs/EXPLAINER-Q2-001.md"):
        text = (ROOT / doc).read_text(encoding="utf-8")
        assert "calibration half" not in text, doc
        assert "half no one looked at" not in text, doc
        assert "half of the history no one" not in text, doc


def test_makefile_says_five_checks():
    line = next(ln for ln in (ROOT / "Makefile").read_text(encoding="utf-8").splitlines() if ln.startswith("signal:"))
    assert "all five checks" in line and "four checks" not in line


def test_controls_comment_matches_computed_n():
    text = (ROOT / "controls.toml").read_text(encoding="utf-8")
    cfg = tomllib.loads(text)
    cells = len(cfg["sweep"]["stop"]) * len(cfg["sweep"]["hold"])
    need = n_for_mean_shift(cfg["floor"]["ev_net_r"] / cfg["power"]["sigma_r"], alpha=cfg["power"]["alpha"] / cells,
                            power=cfg["power"]["power"])
    m = re.search(r"above the ([\d,]+) the plan requires at (\d+) cells", text)
    assert m, "the comment that states the required count is gone"
    assert int(m.group(2)) == cells
    assert int(m.group(1).replace(",", "")) == need
