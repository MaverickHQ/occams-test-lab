"""The chain machinery of the lab's stores (M14.6, split from ``occams/register.py``):
the money type the Register may never hold, the record decorators that refuse it at
declaration time, the canonical serialisation, and ``Store`` — hash-chained, append-only
JSONL. The twenty-three record types live in ``records.py``; the two stores that bind them, ``Register``
and ``Operations``, in the package's ``__init__``. The chain hashes payloads, never code:
nothing in any Register changed when this file was made.
"""

from __future__ import annotations

import copy
import enum
import hashlib
import json
import os
from contextlib import contextmanager
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, ClassVar


@dataclass(frozen=True)
class Money:
    """An amount in an account currency. Belongs in Operations only."""

    amount: float
    currency: str


FORBIDDEN_IN_REGISTER = frozenset({
    "currency", "account_currency", "money", "cash", "balance", "equity",
    "pnl", "pnl_money", "gbp", "usd", "eur", "amount", "notional", "capital"})


class NotPublishable(TypeError):
    """A record class that could carry money was offered to the Register."""


def register_record(cls):
    """Declare a class appendable to the Register. Refuses, at declaration
    time, any field typed Money or named like money — so the assertion
    holds for every instance that can ever exist."""
    if not is_dataclass(cls):
        raise TypeError("register records are frozen dataclasses")
    for f in fields(cls):
        t = f.type if not isinstance(f.type, str) else f.type
        if t is Money or (isinstance(t, str) and "Money" in t):
            raise NotPublishable(f"{cls.__name__}.{f.name} is Money; the Register holds no account currency (S7)")
        if f.name.lower() in FORBIDDEN_IN_REGISTER or any(
                f.name.lower().endswith("_" + w) for w in ("currency", "money", "cash")):
            raise NotPublishable(f"{cls.__name__}.{f.name} names money; the Register holds no account currency (S7)")
    cls.__register_record__ = True
    return cls


def operations_record(cls):
    if not is_dataclass(cls):
        raise TypeError("operations records are frozen dataclasses")
    cls.__operations_record__ = True
    return cls


def now() -> str:
    """An instant, never a date (R10)."""
    return datetime.now(UTC).isoformat(timespec="microseconds")


def _plain(v: Any) -> Any:
    if is_dataclass(v) and not isinstance(v, type):
        return {f.name: _plain(getattr(v, f.name)) for f in fields(v)}
    if isinstance(v, enum.Enum):
        return v.value
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    if isinstance(v, dict):
        return {str(k): _plain(x) for k, x in v.items()}
    return v


def canonical(payload: dict) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


class TamperedHistory(RuntimeError):
    pass


class Store:
    """Hash-chained, append-only JSONL. Subclasses say which record types
    they accept; nothing else is ever written.

    **Append is exclusive and reads the file once** (M16.11; the review's F12). The store's
    own file is locked from reading the tail to the write reaching the disk, so two appenders
    cannot both take the same ``seq``. A store remembers the records it has verified and a
    digest of the bytes they are: the next read hashes those bytes once — a rewrite of any
    of them, of any length, in any clock tick, is refused — and verifies only what was
    appended since. A file shorter than the chain a store has verified is ``truncated``."""

    marker: ClassVar[str] = ""
    name: ClassVar[str] = "store"

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._verified: list[dict] = []          # the lines this store has verified, in order
        self._length = 0                         # how many bytes of the file they are
        self._hasher = hashlib.sha256()          # over exactly those bytes

    # ---- reading: one read of the file, the verified prefix by digest, the tail by chain ----

    def _read(self) -> bytes:
        return self.path.read_bytes() if self.path.exists() else b""

    def _parse(self, data: bytes) -> list[dict]:
        try:
            return [json.loads(line) for line in data.decode("utf-8").splitlines() if line.strip()]
        except ValueError as e:
            raise TamperedHistory(f"{self.name}: a line is not a record ({e})") from None

    def _lines(self) -> list[dict]:
        return self._parse(self._read())

    @staticmethod
    def _digest(prev: str, seq: int, payload: dict) -> str:
        return hashlib.sha256(f"{prev}|{seq}|{canonical(payload)}".encode()).hexdigest()

    def _check(self, lines: list[dict], *, start: int, prev: str) -> None:
        for i, line in enumerate(lines, start):
            if line.get("seq") != i or line.get("prev") != prev:
                raise TamperedHistory(f"{self.name}: chain broken at seq {i}")
            if line.get("sha") != self._digest(prev, i, line["payload"]):
                raise TamperedHistory(f"{self.name}: record {i} was rewritten")
            prev = line["sha"]

    def _truncated(self, data: bytes) -> None:
        if len(data) < self._length:
            raise TamperedHistory(f"{self.name}: truncated — the file is {self._length - len(data)} bytes shorter than the "
                                  f"{len(self._verified)} records this store verified")

    def _remember(self, lines: list[dict], data: bytes) -> None:
        self._verified, self._length, self._hasher = lines, len(data), hashlib.sha256(data)

    def _sync(self) -> list[dict]:
        """The verified chain, brought up to the file with one read: the bytes already
        verified by their digest, whatever follows them by the chain."""
        data = self._read()
        self._truncated(data)
        if hashlib.sha256(data[:self._length]).digest() != self._hasher.digest():
            self._check(self._parse(data), start=0, prev="genesis")          # names the record, when the chain itself is broken
            raise TamperedHistory(f"{self.name}: the {len(self._verified)} records this store verified were replaced")
        if len(data) > self._length:
            tail = self._parse(data[self._length:])
            self._check(tail, start=len(self._verified), prev=self._verified[-1]["sha"] if self._verified else "genesis")
            self._remember(self._verified + tail, data)
        return self._verified

    def verify(self) -> int:
        """Walk the whole chain, from the file. Returns the number of records, or raises."""
        data = self._read()
        self._truncated(data)
        lines = self._parse(data)
        self._check(lines, start=0, prev="genesis")
        if len(lines) < len(self._verified) or any(a["sha"] != b["sha"] for a, b in zip(self._verified, lines, strict=False)):
            raise TamperedHistory(f"{self.name}: truncated or replaced — the {len(self._verified)} records this store verified "
                                  f"are not the first records of the file")
        self._remember(lines, data)
        return len(lines)

    # ---- appending: exclusive, from reading the tail to the write reaching the disk ----

    @contextmanager
    def _exclusive(self):
        with self.path.open("ab") as f:
            _lock(f)
            try:
                yield f
            finally:
                _unlock(f)

    def append(self, record: Any) -> dict:
        if not getattr(type(record), self.marker, False):
            raise TypeError(f"{type(record).__name__} is not a {self.name} record")
        with self._exclusive() as f:
            lines = self._sync()  # a tampered file cannot be extended, and a rival's append is read before this one is numbered
            n = len(lines)
            prev = lines[-1]["sha"] if n else "genesis"
            payload = {"type": type(record).__name__, "at": now(), **_plain(record)}
            line = {"seq": n, "prev": prev, "payload": payload, "sha": self._digest(prev, n, payload)}
            data = (canonical(line) + "\n").encode("utf-8")
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
            self._verified = lines + [json.loads(data)]     # as a reader will parse it
            self._length += len(data)
            self._hasher.update(data)
        return line

    def records(self) -> list[dict]:
        return [copy.deepcopy(line["payload"]) for line in self._sync()]

    def chain(self) -> list[dict]:
        """Every line with its seq, prev and sha — verified first. What a
        renderer reads when it must show the chain and not only the payloads."""
        return copy.deepcopy(self._sync())


# ---- the lock: the store's own file, exclusively ------------------------------------------------------

try:
    import fcntl

    def _lock(f) -> None:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)

    def _unlock(f) -> None:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

except ImportError:  # pragma: no cover — a system without POSIX locks: the first byte, through the C runtime
    import msvcrt

    def _lock(f) -> None:
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)

    def _unlock(f) -> None:
        f.seek(0)
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
