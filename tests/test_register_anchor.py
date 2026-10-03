"""M16.4 / ADR-0054 — the heads of the committed stores are pinned.

The chain shows that one line was not changed without the rest. It does not show that
the file is the one that was written: a copy with one outcome flipped and every digest
recomputed verifies, and so does a copy cut short. Against a pinned count and head both
fail — and a pin is moved only by the command that names it.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path

from occams.register import heads
from occams.register.store import Store, canonical

ROOT = Path(__file__).resolve().parent.parent


def _lab(tmp_path: Path) -> tuple[Path, Path]:
    """A scratch root holding a copy of programme 2's Register, pinned as it stands."""
    (tmp_path / "register").mkdir()
    store = tmp_path / "register" / "programme-2.jsonl"
    shutil.copy(ROOT / "register" / "programme-2.jsonl", store)
    pin = tmp_path / "register" / "HEADS.toml"
    heads.pin(pin, [store], root=tmp_path)
    return store, pin


def test_committed_registers_match_pinned_heads():
    pin = ROOT / "register" / "HEADS.toml"
    assert heads.check(pin, root=ROOT) == []
    pinned = {e["path"] for e in heads.load(pin)}
    committed = {f"register/{p.name}" for p in (ROOT / "register").glob("*.jsonl")}
    assert pinned == committed, "every committed store is pinned, and nothing else is"


def test_forged_and_rechained_register_fails_against_pin(tmp_path):
    store, pin = _lab(tmp_path)
    lines = [json.loads(ln) for ln in store.read_text(encoding="utf-8").splitlines() if ln.strip()]
    target = next(ln for ln in lines if ln["payload"].get("type") == "HypothesisResolved" and ln["payload"].get("hypothesis_id") == "Q2-002")
    assert target["payload"]["outcome"] == "null"
    target["payload"]["outcome"] = "supported"
    prev = "genesis"
    for seq, ln in enumerate(lines):
        ln["prev"] = prev
        ln["sha"] = hashlib.sha256(f"{prev}|{seq}|{canonical(ln['payload'])}".encode()).hexdigest()
        prev = ln["sha"]
    store.write_text("\n".join(canonical(ln) for ln in lines) + "\n", encoding="utf-8")
    assert Store(store).verify() == 37, "the chain alone accepts the forgery — that is the defect"
    problems = heads.check(pin, root=tmp_path)
    assert len(problems) == 1 and "rewritten" in problems[0] and "programme-2.jsonl" in problems[0]


def test_truncated_register_fails_against_pinned_count(tmp_path):
    store, pin = _lab(tmp_path)
    store.write_text("\n".join(store.read_text(encoding="utf-8").splitlines()[:20]) + "\n", encoding="utf-8")
    assert Store(store).verify() == 20, "the chain alone accepts the truncation"
    problems = heads.check(pin, root=tmp_path)
    assert len(problems) == 1 and "truncated" in problems[0] and "20" in problems[0] and "37" in problems[0]


def test_a_store_that_is_not_pinned_and_a_pin_with_no_store_are_both_named(tmp_path):
    store, pin = _lab(tmp_path)
    extra = tmp_path / "register" / "other.jsonl"
    shutil.copy(store, extra)
    assert any("not pinned" in p and "other.jsonl" in p for p in heads.check(pin, root=tmp_path))
    extra.unlink()
    store.unlink()
    assert any("missing" in p and "programme-2.jsonl" in p for p in heads.check(pin, root=tmp_path))


def test_the_pin_moves_only_by_the_command_and_keeps_an_unchanged_stores_date(tmp_path):
    store, pin = _lab(tmp_path)
    before = heads.load(pin)[0]
    assert (before["count"], len(before["head"])) == (37, 64)
    heads.pin(pin, [store], root=tmp_path)                       # nothing changed: the entry, date included, is kept
    assert heads.load(pin)[0] == before
    assert heads.main(["check", "--heads", str(pin), "--root", str(tmp_path)]) == 0
    store.write_text("\n".join(store.read_text(encoding="utf-8").splitlines()[:20]) + "\n", encoding="utf-8")
    assert heads.main(["check", "--heads", str(pin), "--root", str(tmp_path)]) == 1
