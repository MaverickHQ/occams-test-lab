"""M16.3 — the documents say what the code does (the review's F22, and the wording half of F08).

The partitions are cut 30 / 50 / 20, oldest first; "half" was never true of either. The
signal control names five checks since ADR-0043. The controls' comment states the count
the plan computes, not one remembered.
"""

from __future__ import annotations

import re
import tomllib
from pathlib import Path

from occams.inference import one_sided_n

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
    # ADR-0050: the control plans one-sided against its apparatus alternative; before it, the floor against nil (837)
    need = one_sided_n(cfg["power"]["sigma_r"], cfg["power"]["alternative_ev_net_r"] - cfg["floor"]["ev_net_r"],
                       alpha=cfg["power"]["alpha"] / cells, power=cfg["power"]["power"])
    m = re.search(r"above the ([\d,]+) the plan requires at (\d+) cells", text)
    assert m, "the comment that states the required count is gone"
    assert int(m.group(2)) == cells
    assert int(m.group(1).replace(",", "")) == need


def test_claude_md_is_small():
    """M16.12 (the review's F25): the project context an agent reads first had grown to forty-three kilobytes of
    history in paragraphs a thousand characters long. The history is the task list's status log; this file is the
    rules and where to look — under five kilobytes, no line over two hundred characters, and still naming every rule."""
    text = (ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert len(text.encode("utf-8")) < 5000, len(text.encode("utf-8"))
    assert max(len(line) for line in text.splitlines()) <= 200
    flat = " ".join(text.split())
    for rule in ("author's alone", "never committed", "Append, never overwrite", "`register --yes`", "`APPROVED -> LIVE`",
                 "vendored and never edited", "never goes to `origin`", "never merge on GitHub's side", "History is never rewritten",
                 "never set it as a remote", "must refuse", "must accept", "TASKS-v4.md"):
        assert rule in flat, rule
