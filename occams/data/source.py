"""The ``DataSource`` port (M4.1). A source hands back rows in a declared
schema; parsing, rights, the symbol budget and archiving happen here, so a
source knows nothing about what happens to what it fetched.

The committed fixture is synthetic bars in Tiingo's response schema — the
parser is exercised without a single vendor row in the repository (raw
redistribution is forbidden, M0.3). The live source needs ``TIINGO_API_KEY``
in the environment (R5): there is no parameter for it and no default.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Protocol

from occams.data.actions import Action, ActionKind, ActionSeries
from occams.data.archive import BarArchive
from occams.data.bars import Bars
from occams.data.instants import session_close
from occams.data.rights import REGISTRY, Rights, Use, require

TIINGO_FIELDS = ("date", "open", "high", "low", "close", "volume", "adjOpen", "adjHigh", "adjLow",
                 "adjClose", "adjVolume", "divCash", "splitFactor")


class DataSource(Protocol):
    source_id: str

    def fetch(self, symbol: str, start: date, end: date) -> list[dict]: ...


class SourceError(RuntimeError):
    pass


class RateLimited(SourceError):
    """The vendor's hourly request allocation is spent (HTTP 429). Not a
    property of the symbol: the next request fails the same way, so a batch
    stops here rather than charging the ledger for names it cannot fetch."""


def parse_tiingo(symbol: str, rows: list[dict], *, venue: str = "NYSE", day_offset: int = 0
                 ) -> tuple[Bars, ActionSeries]:
    """As-printed OHLC from ``open/high/low/close`` — Tiingo's raw fields —
    with the dividend and split columns lifted into the action series. Day
    ordinals are calendar ordinals shared by every series; close instants are
    the venue's session close on the row's date."""
    if not rows:
        raise SourceError(f"{symbol}: no rows")
    rows = sorted(rows, key=lambda r: r["date"])
    for r in rows:
        missing = [f for f in ("date", "open", "high", "low", "close", "volume") if f not in r]
        if missing:
            raise SourceError(f"{symbol}: row {r.get('date')} lacks {missing} — full OHLC is required (F18.2)")
    dates = [datetime.fromisoformat(r["date"].replace("Z", "+00:00")).date() for r in rows]
    # `day` is the calendar ordinal (date.toordinal()), not a per-series index: every
    # archived series shares one clock, so partitions cut on one boundary across names
    days = tuple(day_offset + d.toordinal() for d in dates)
    bars = Bars(symbol, tuple(float(r["open"]) for r in rows), tuple(float(r["high"]) for r in rows),
                tuple(float(r["low"]) for r in rows), tuple(float(r["close"]) for r in rows),
                tuple(float(r["volume"]) for r in rows), days,
                close_at=tuple(session_close(d, venue).isoformat() for d in dates))
    acts = []
    for i, r in enumerate(rows):
        sf = float(r.get("splitFactor", 1.0) or 1.0)
        if sf != 1.0:
            acts.append(Action(ActionKind.SPLIT, symbol, days[i], ratio=sf, provenance="tiingo splitFactor"))
        dv = float(r.get("divCash", 0.0) or 0.0)
        if dv > 0:
            acts.append(Action(ActionKind.DIVIDEND, symbol, days[i], amount=dv, provenance="tiingo divCash"))
    return bars, ActionSeries(tuple(acts))


@dataclass
class FixtureSource:
    """Synthetic rows in Tiingo's schema, committed under tests/fixtures/."""

    path: Path
    source_id: str = "synthetic"

    def fetch(self, symbol: str, start: date, end: date) -> list[dict]:
        data = json.loads(Path(self.path).read_text(encoding="utf-8"))
        if symbol not in data:
            raise SourceError(f"{symbol} is not in the fixture")
        return [r for r in data[symbol] if str(start) <= r["date"][:10] <= str(end)]


@dataclass
class CsvSource:
    """A user's own daily bars (M15.5): one CSV per symbol under ``path``
    (``<path>/<SYMBOL>.csv``), or ``path`` itself for a single symbol, with the
    columns ``date, open, high, low, close, volume`` and, optionally,
    ``dividend`` (cash per share, ex-date row) and ``split`` (factor). Rows come
    out in the live source's schema so the same parser, the same auditors and
    the same archive apply. Its rights are the user's to declare at ingest —
    a CSV carries no licence, and an undeclared right is a refusal."""

    path: Path
    source_id: str

    _REQUIRED = ("date", "open", "high", "low", "close", "volume")
    _OPTIONAL = {"dividend": "divCash", "divcash": "divCash", "split": "splitFactor", "splitfactor": "splitFactor"}

    def fetch(self, symbol: str, start: date, end: date) -> list[dict]:
        import csv

        p = Path(self.path)
        f = p if p.is_file() else p / f"{symbol}.csv"
        if not f.exists():
            raise SourceError(f"{symbol}: no CSV at {f}")
        with f.open(newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            if reader.fieldnames is None:
                raise SourceError(f"{symbol}: {f} has no header row")
            names = {n.strip().lower(): n for n in reader.fieldnames}
            missing = [c for c in self._REQUIRED if c not in names]
            if missing:
                raise SourceError(f"{symbol}: {f} lacks the column(s) {missing} — date, open, high, low, close, volume are required (F18.2)")
            rows = []
            for r in reader:
                d = r[names["date"]].strip()[:10]
                if not (str(start) <= d <= str(end)):
                    continue
                row = {"date": d, **{c: float(r[names[c]]) for c in ("open", "high", "low", "close", "volume")}}
                for col, tiingo in self._OPTIONAL.items():
                    if col in names and r[names[col]] not in ("", None):
                        row[tiingo] = float(r[names[col]])
                rows.append(row)
        return rows


@dataclass
class TiingoSource:
    """The live pull. Separate and optional (M4.1); never runs in tests."""

    source_id: str = "tiingo-starter"
    base_url: str = "https://api.tiingo.com/tiingo/daily"

    def fetch(self, symbol: str, start: date, end: date) -> list[dict]:
        import urllib.error
        import urllib.parse
        import urllib.request

        token = os.environ.get("TIINGO_API_KEY")
        if not token:
            raise SourceError("TIINGO_API_KEY is not set; the live source has no default and no parameter (R5)")
        q = urllib.parse.urlencode({"startDate": str(start), "endDate": str(end), "format": "json"})
        req = urllib.request.Request(f"{self.base_url}/{urllib.parse.quote(symbol)}/prices?{q}",
                                     headers={"Authorization": f"Token {token}", "User-Agent": "occams-test-lab"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 — https, fixed host
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            # the vendor's answer for a symbol it does not hold is a refusal by name, not a traceback
            # (M12.1b); the message carries the status and the vendor's own words, never the token (R5)
            kind = RateLimited if e.code == 429 else SourceError
            raise kind(f"{symbol}: the source answered HTTP {e.code} — {_vendor_detail(e)}") from None
        except urllib.error.URLError as e:
            raise SourceError(f"{symbol}: the source could not be reached — {e.reason}") from None


def _vendor_detail(e) -> str:
    """The vendor's own words for a refusal, from its JSON ``detail`` when it
    sends one, else the first line of the body, else the HTTP reason."""
    try:
        body = e.read().decode("utf-8", "replace")[:300].strip()
    except OSError:
        return str(e.reason)
    try:
        d = json.loads(body)
    except ValueError:
        return body.splitlines()[0] if body else str(e.reason)
    return str(d.get("detail", body)) if isinstance(d, dict) else body


class BudgetExceeded(RuntimeError):
    pass


class SymbolBudget:
    """Tiingo Starter allows 500 unique symbols a month (M0.3). The 501st is
    a refusal at ingest, not a surprise at month end."""

    def __init__(self, path: Path, *, limit: int):
        self.path = Path(path)
        self.limit = int(limit)

    def _load(self) -> dict[str, list[str]]:
        if not self.path.exists():
            return {}
        return json.loads(self.path.read_text(encoding="utf-8"))

    def used(self, month: str) -> list[str]:
        return list(self._load().get(month, []))

    def charge(self, symbol: str, month: str) -> None:
        data = self._load()
        seen = data.setdefault(month, [])
        if symbol in seen:
            return
        if len(seen) >= self.limit:
            raise BudgetExceeded(f"{month}: {self.limit} unique symbols already used this month; "
                                 f"{symbol} would be number {len(seen) + 1}")
        seen.append(symbol)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")


@dataclass(frozen=True)
class Ingested:
    bars: Bars
    actions: ActionSeries
    sha: str
    rights: Rights


def ingest(source: DataSource, symbol: str, start: date, end: date, *, archive: BarArchive,
           budget: SymbolBudget | None, month: str, registry=REGISTRY, venue: str = "NYSE") -> Ingested:
    """Rights first, budget second, fetch third, archive last. A source
    without recorded rights never reaches the network."""
    known = {**archive.rights_registry(), **dict(registry)} if hasattr(archive, "rights_registry") else registry
    rights = require(source.source_id, Use.PRIVATE_RETENTION, known)
    if budget is not None:
        budget.charge(symbol, month)
    rows = source.fetch(symbol, start, end)
    bars, actions = parse_tiingo(symbol, rows, venue=venue)
    sha = archive.put(bars, actions, source_id=source.source_id, requested_start=start, requested_end=end, registry=known)
    return Ingested(bars, actions, sha, rights)


def export(bars: Bars, *, source_id: str, use: Use, registry=REGISTRY) -> Bars:
    """Leaving the private boundary is a use; the recorded rights decide."""
    require(source_id, use, registry)
    return bars
