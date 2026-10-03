"""M16.11 (the review's F12) — append is exclusive and reads the file once.

``append`` used to verify the whole chain, read the file again for its tail, and then
write, with nothing held in between: two appenders that both read ``n`` both wrote
``seq n`` and forked the chain. And every append and every ``records()`` re-read and
re-hashed every record, three reads at a time."""

from __future__ import annotations

import builtins
import io
import multiprocessing
import threading
from pathlib import Path

import pytest

from occams.register import RefusalRecorded, Register, TamperedHistory
from occams.register import store as store_module


def _rec(text: str) -> RefusalRecorded:
    return RefusalRecorded("a->b", text, {}, None, None)


def test_concurrent_appends_never_fork_chain(tmp_path, monkeypatch):
    """A second appender arrives after the first has read the tail and before it has
    written — the moment the chain used to fork. Now the second waits for the first's lock,
    reads the tail the first wrote, and takes the next seq."""
    path = tmp_path / "r.jsonl"
    first = Register(path)
    first.append(_rec("zero"))
    real_now = store_module.now
    other: list[threading.Thread] = []
    errors: list[BaseException] = []

    def second_appender():
        try:
            Register(path).append(_rec("from the second appender"))
        except BaseException as e:  # noqa: BLE001 — reported by the assertion below
            errors.append(e)

    def now_with_a_rival():
        if not other:                                   # once: between the first appender's read and its write
            t = threading.Thread(target=second_appender)
            other.append(t)
            t.start()
            t.join(timeout=0.5)                         # unlocked, it finishes here; locked, it is still waiting
        return real_now()

    monkeypatch.setattr(store_module, "now", now_with_a_rival)
    first.append(_rec("from the first appender"))
    other[0].join(timeout=10)
    assert not other[0].is_alive() and errors == []
    fresh = Register(path)
    assert fresh.verify() == 3
    assert [line["seq"] for line in fresh.chain()] == [0, 1, 2]
    assert [r["reason"] for r in fresh.records()] == ["zero", "from the first appender", "from the second appender"]
    assert first.verify() == 3 and [r["reason"] for r in first.records()][-1] == "from the second appender"


def _append_many(args):
    path, who, count = args
    reg = Register(Path(path))
    for i in range(count):
        reg.append(RefusalRecorded("a->b", f"{who}-{i}", {}, None, None))
    return who


def test_four_processes_appending_at_once_leave_one_chain(tmp_path):
    path = tmp_path / "r.jsonl"
    with multiprocessing.get_context("spawn").Pool(4) as pool:
        assert sorted(pool.map(_append_many, [(str(path), w, 25) for w in "abcd"])) == list("abcd")
    reg = Register(path)
    assert reg.verify() == 100 and [line["seq"] for line in reg.chain()] == list(range(100))
    assert sorted(r["reason"] for r in reg.records()) == sorted(f"{w}-{i}" for w in "abcd" for i in range(25))


class _Reads:
    """Counts every time ``path`` is opened to be read, however it is opened."""

    def __init__(self, monkeypatch, path: Path):
        self.count, self._path = 0, str(path)
        real = io.open

        def counting(file, mode="r", *args, **kwargs):
            if str(file) == self._path and ("r" in mode or "+" in mode):
                self.count += 1
            return real(file, mode, *args, **kwargs)

        monkeypatch.setattr(io, "open", counting)
        monkeypatch.setattr(builtins, "open", counting)


def test_append_reads_file_at_most_once_after_warm_cache(tmp_path, monkeypatch):
    reg = Register(tmp_path / "r.jsonl")
    for i in range(20):
        reg.append(_rec(str(i)))
    reads = _Reads(monkeypatch, reg.path)
    for i in range(20, 40):
        reg.append(_rec(str(i)))
    assert reads.count <= 20, f"{reads.count} reads for 20 appends"
    before = reads.count
    assert len(reg.records()) == 40 and len(reg.records()) == 40 and len(reg.chain()) == 40
    assert reads.count - before <= 3                    # a read of the records is one read of the file, not a re-verification
    assert Register(reg.path).verify() == 40


def test_only_the_appended_tail_is_verified_again(tmp_path, monkeypatch):
    """Once a prefix is verified its records are not hashed again — only what was appended since."""
    reg = Register(tmp_path / "r.jsonl")
    for i in range(30):
        reg.append(_rec(str(i)))
    hashed = []
    real = Register._digest
    monkeypatch.setattr(Register, "_digest", staticmethod(lambda prev, seq, payload: hashed.append(seq) or real(prev, seq, payload)))
    Register(reg.path).append(_rec("by another"))       # verifies all thirty, hashes its own
    assert sorted(hashed) == list(range(31))
    del hashed[:]
    reg.append(_rec("thirty-one"))                       # this store verifies the one record it has not seen, and hashes its own
    assert sorted(hashed) == [30, 31]
    assert len(reg.records()) == 32 and hashed == [30, 31]


def test_shrinking_file_raises_truncated(tmp_path):
    """Whole records removed from the end still chain — the review's forgery by truncation.
    A store that has verified more than the file now holds says so, by name."""
    reg = Register(tmp_path / "r.jsonl")
    for i in range(5):
        reg.append(_rec(str(i)))
    lines = reg.path.read_text().splitlines(keepends=True)
    reg.path.write_text("".join(lines[:3]))
    assert Register(reg.path).verify() == 3              # a fresh reader cannot tell: the pinned heads catch that (ADR-0054)
    for act in (reg.verify, reg.records, reg.chain, lambda: reg.append(_rec("after"))):
        with pytest.raises(TamperedHistory, match="truncated"):
            act()
    assert len(reg.path.read_text().splitlines()) == 3   # and nothing was appended to it


def test_a_prefix_rewritten_under_a_warm_store_is_refused_even_at_the_same_size(tmp_path):
    """The cache is keyed by the bytes it verified, not by a timestamp: a rewrite of the same
    length in the same clock tick is still a rewrite."""
    reg = Register(tmp_path / "r.jsonl")
    reg.append(_rec("one"))
    reg.append(_rec("two"))
    reg.path.write_text(reg.path.read_text().replace('"reason":"one"', '"reason":"won"'))
    for act in (reg.records, lambda: reg.append(_rec("three"))):
        with pytest.raises(TamperedHistory):
            act()
    assert len(reg.path.read_text().splitlines()) == 2
