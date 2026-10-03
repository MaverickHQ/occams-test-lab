"""M11.7 — the publication gate's check catches each listed defect on a
page and a Register, independently of the renderer. Fixtures are
assembled at runtime so this file does not itself trip the scan."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


def _load():
    spec = importlib.util.spec_from_file_location("_prepublish", ROOT / "tools" / "prepublish.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


CLEAN = "<!doctype html><html><head><meta charset=\"utf-8\"><title>t</title></head><body><main><p>EV +0.05 net R on 2003-03-02</p></main></body></html>"


@pytest.mark.parametrize("label,planted", [
    ("a <script>", "<scr" + "ipt>alert(1)</scr" + "ipt>"),
    ("a network reference", "<a href=\"htt" + "ps://example.test/x\">x</a>"),
    ("a credential-shaped string", "AKIA" + "EXAMPLEKEY123456"),
    ("a broker's or venue's term", "commission at " + "Trading " + "212"),
    ("dated rows with four prices", "".join(f"<tr><td>2003-03-{d:02d}</td><td>100.1</td><td>101.2</td><td>99.3</td><td>100.4</td></tr>" for d in range(1, 15))),
])
def test_each_page_defect_is_refused_by_name(label, planted):
    pp = _load()
    assert pp.check_page(CLEAN) == []
    problems = pp.check_page(CLEAN.replace("</main>", planted + "</main>"), name="p")
    assert problems and any(label in x for x in problems), problems


def test_a_handful_of_dated_prices_is_a_fact_not_a_dataset():
    pp = _load()
    rows = "".join(f"<tr><td>2003-03-{d:02d}</td><td>100.1</td><td>101.2</td><td>99.3</td><td>100.4</td></tr>" for d in range(1, 6))
    assert pp.check_page(CLEAN.replace("</main>", rows + "</main>")) == []


def test_a_register_with_a_money_key_or_a_credential_is_refused(tmp_path):
    pp = _load()
    ok = json.dumps({"seq": 0, "prev": "genesis", "payload": {"type": "HypothesisRegistered", "hypothesis_id": "Q-1", "alpha_spent": 0.4}, "sha": "x"})
    assert pp.check_register(ok + "\n") == []
    money = json.dumps({"seq": 1, "prev": "x", "payload": {"type": "Odd", "starting_" + "capital": 1}, "sha": "y"})
    problems = pp.check_register(ok + "\n" + money + "\n", name="r")
    assert problems and "names money" in problems[0]
    cred = json.dumps({"seq": 1, "prev": "x", "payload": {"type": "Odd", "note": "ghp_" + "a" * 36}, "sha": "y"})
    assert any("credential" in x for x in pp.check_register(ok + "\n" + cred + "\n"))
    bad = tmp_path / "r.jsonl"
    bad.write_text(ok + "\n" + money + "\n", encoding="utf-8")
    assert pp.main([str(bad)]) == 1


def test_the_committed_pages_and_registers_pass():
    pp = _load()
    targets = [t for t in pp.default_targets() if t.exists()]
    assert targets and pp.main([str(t) for t in targets]) == 0


def test_the_whole_tree_scan_names_every_hit_and_keeps_one_only_by_recorded_decision(tmp_path):
    """M15.3: broker terms, money figures, private paths, e-mail addresses and account ids across committed text; a hit is
    removed or kept by the author's recorded decision, never excused silently; the scanner itself is exempt from the
    broker check because it names the terms it refuses."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_pp", ROOT / "tools" / "prepublish.py")
    pp = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pp)
    f = tmp_path / "notes.md"
    f.write_text("A note about Trading 212 and a cap of $129.17 kept in ~/Documents/x and mailed to a@b.io from account 123456789012 yesterday.\n")
    unresolved, kept = pp.scan_tree([f], decisions=[], root=tmp_path)
    assert {h["check"] for h in unresolved} == {"broker term (R6)", "money figure", "private path", "e-mail address", "account identifier"}
    assert kept == [] and all(h["file"] == "notes.md" and h["line"] == 1 for h in unresolved)
    decisions = [{"file": "notes.md", "check": "money figure", "match": "$129.17", "by": "author", "date": "2026-09-25", "reason": "the cap is public"},
                 {"file": "notes.md", "check": "e-mail address", "match": "*", "by": "author", "date": "2026-09-25"}]
    unresolved, kept = pp.scan_tree([f], decisions=decisions, root=tmp_path)
    assert {h["check"] for h in kept} == {"money figure", "e-mail address"} and all(h["by"] == "author" for h in kept)
    assert {h["check"] for h in unresolved} == {"broker term (R6)", "private path", "account identifier"}
    # the scanner names the terms it refuses and is exempt from its own broker check
    files = pp.committed_text_files()
    assert any(p.name == "prepublish.py" for p in files)
    own = pp.scan_tree([ROOT / "tools" / "prepublish.py", ROOT / "tests" / "test_prepublish.py"], decisions=[])[0]
    assert own == []
