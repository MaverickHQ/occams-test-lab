"""The chain machinery of the lab's stores (M14.6, split from ``occams/register.py``):
the money type the Register may never hold, the record decorators that refuse it at
declaration time, the canonical serialisation, and ``Store`` — hash-chained, append-only
JSONL. The twenty-one record types live in ``records.py``; the two stores that bind them, ``Register``
and ``Operations``, in the package's ``__init__``. The chain hashes payloads, never code:
nothing in any Register changed when this file was made.
"""

from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from datetime import datetime, timezone
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
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


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
    they accept; nothing else is ever written."""

    marker: ClassVar[str] = ""
    name: ClassVar[str] = "store"

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def _lines(self) -> list[dict]:
        if not self.path.exists():
            return []
        return [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    @staticmethod
    def _digest(prev: str, seq: int, payload: dict) -> str:
        return hashlib.sha256(f"{prev}|{seq}|{canonical(payload)}".encode("utf-8")).hexdigest()

    def verify(self) -> int:
        """Walk the chain. Returns the number of records, or raises."""
        prev = "genesis"
        for i, line in enumerate(self._lines()):
            if line.get("seq") != i or line.get("prev") != prev:
                raise TamperedHistory(f"{self.name}: chain broken at seq {i}")
            if line.get("sha") != self._digest(prev, i, line["payload"]):
                raise TamperedHistory(f"{self.name}: record {i} was rewritten")
            prev = line["sha"]
        return i + 1 if self._lines() else 0

    def append(self, record: Any) -> dict:
        if not getattr(type(record), self.marker, False):
            raise TypeError(f"{type(record).__name__} is not a {self.name} record")
        n = self.verify()  # a tampered file cannot be extended
        prev = self._lines()[-1]["sha"] if n else "genesis"
        payload = {"type": type(record).__name__, "at": now(), **_plain(record)}
        line = {"seq": n, "prev": prev, "payload": payload, "sha": self._digest(prev, n, payload)}
        with self.path.open("a", encoding="utf-8") as f:
            f.write(canonical(line) + "\n")
        return line

    def records(self) -> list[dict]:
        self.verify()
        return [line["payload"] for line in self._lines()]

    def chain(self) -> list[dict]:
        """Every line with its seq, prev and sha — verified first. What a
        renderer reads when it must show the chain and not only the payloads."""
        self.verify()
        return self._lines()
