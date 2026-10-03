"""The archive stores the bars (D12, ADR-0021, M4.8): content-addressed,
immutable, with a hash-chained manifest. Reproduction reads the archive
and never the vendor; a vendor revision produces a new hash beside the old
one and can alter nothing already recorded.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

from occams.data.actions import Action, ActionKind, ActionSeries
from occams.data.bars import Bars
from occams.data.rights import REGISTRY, Answer, Rights, Use, require
from occams.register import Store, _plain, canonical, now


def archive_record(cls):
    cls.__archive_record__ = True
    return cls


@archive_record
@dataclass(frozen=True)
class Archived:
    sha: str
    source_id: str
    name: str
    first_day: int
    last_day: int
    bars: int
    actions: int
    fetched_at: str
    first_at: str = ""   # the first bar's close instant
    last_at: str = ""
    requested_start: str = ""  # the span that was ASKED for — a vendor's history may start later than that
    requested_end: str = ""


class Manifest(Store):
    marker: ClassVar[str] = "__archive_record__"
    name: ClassVar[str] = "Archive manifest"
    Archived = Archived


class NotArchived(KeyError):
    pass


def _encode(bars: Bars, actions: ActionSeries) -> str:
    payload = {"bars": _plain(bars), "actions": _plain(actions)}
    return canonical(payload)


def _decode(text: str) -> tuple[Bars, ActionSeries]:
    d = json.loads(text)
    b = d["bars"]
    bars = Bars(b["name"], tuple(b["open"]), tuple(b["high"]), tuple(b["low"]), tuple(b["close"]),
                tuple(b["volume"]), tuple(b["day"]),
                close_at=None if b.get("close_at") is None else tuple(b["close_at"]))
    acts = ActionSeries(tuple(Action(ActionKind(a["kind"]), a["name"], a["day"], a.get("ratio"), a.get("amount"),
                                     a.get("terms"), a.get("provenance", "")) for a in d["actions"]["actions"]))
    return bars, acts


class BarArchive:
    def __init__(self, root: Path):
        self.root = Path(root)
        (self.root / "bars").mkdir(parents=True, exist_ok=True)
        self.manifest = Manifest(self.root / "manifest.jsonl")

    def put(self, bars: Bars, actions: ActionSeries, *, source_id: str, requested_start=None,
            requested_end=None, registry=None) -> str:
        """Store; return the content hash. Idempotent for identical content;
        different content is a different hash — nothing is ever overwritten.
        The manifest records the span that was asked for as well as the
        span received, so a later ingest can tell "the vendor has nothing
        earlier" from "nobody asked for earlier"."""
        require(source_id, Use.PRIVATE_RETENTION, self.rights_registry() if registry is None else registry)
        text = _encode(bars, actions)
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        path = self.root / "bars" / f"{sha}.json"
        if path.exists():
            if path.read_text(encoding="utf-8") != text:
                raise RuntimeError(f"archive corruption: {sha} exists with different content")
        else:
            path.write_text(text, encoding="utf-8")
        # the manifest records every put — a refresh that returns identical bytes
        # still records that the span was asked for again, under the same sha
        first_at = bars.close_at[0] if bars.close_at else ""
        last_at = bars.close_at[-1] if bars.close_at else ""
        self.manifest.append(Archived(sha, source_id, bars.name, bars.day[0] if bars.n else 0,
                                      bars.day[-1] if bars.n else 0, bars.n, len(actions.actions), now(),
                                      first_at, last_at, str(requested_start or ""), str(requested_end or "")))
        return sha

    def latest_for(self, name: str) -> dict | None:
        rows = [e for e in self.entries() if e["name"] == name]
        return rows[-1] if rows else None

    def covers(self, name: str, start, end, *, slack_days: int = 5) -> dict | None:
        """The latest archived series for ``name`` if it already spans
        [start, end] to within ``slack_days`` at each end (trading calendars
        start a few days after a requested date). None means fetch."""
        from datetime import datetime, timedelta

        e = self.latest_for(name)
        if not e or not e.get("last_at"):
            return None
        # the start is covered if it was ASKED for at or before `start` (the
        # vendor's history may begin later than anyone asked); the end is
        # covered if the last bar is within a few days of `end`
        if e.get("requested_start"):
            start_ok = datetime.fromisoformat(e["requested_start"]).date() <= start
        elif e.get("first_at"):
            start_ok = datetime.fromisoformat(e["first_at"]).date() <= start + timedelta(days=slack_days)
        else:
            return None
        last = datetime.fromisoformat(e["last_at"]).date()
        return e if start_ok and last >= end - timedelta(days=slack_days) else None

    def get(self, sha: str) -> tuple[Bars, ActionSeries]:
        """Reads the archive and nothing else."""
        path = self.root / "bars" / f"{sha}.json"
        if not path.exists():
            raise NotArchived(f"{sha} is not in the archive — reproduction never fetches")
        text = path.read_text(encoding="utf-8")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != sha:
            raise RuntimeError(f"archive corruption: {sha} does not hash to its name")
        return _decode(text)

    def entries(self) -> list[dict]:
        return self.manifest.records()

    # ---- content-addressed blobs beside the bars: path distributions (M8.5) ----

    def put_blob(self, kind: str, payload: dict) -> str:
        (self.root / kind).mkdir(parents=True, exist_ok=True)
        text = canonical(payload)
        sha = hashlib.sha256(text.encode("utf-8")).hexdigest()
        path = self.root / kind / f"{sha}.json"
        if not path.exists():
            path.write_text(text, encoding="utf-8")
        return sha

    def rights_registry(self) -> dict[str, Rights]:
        """The code's rights records and every one declared into this archive
        under ``rights/`` (M15.5: a user's own bars, in the user's words) — the
        registry the archive stores under. A declared record never overrides
        the code's for the same source id."""
        declared: list[Rights] = []
        d = self.root / "rights"
        if d.is_dir():
            for p in sorted(d.glob("*.json")):
                try:
                    r = json.loads(p.read_text(encoding="utf-8"))
                    declared.append(Rights(source_id=str(r["source_id"]), recorded_on=str(r["recorded_on"]), provenance=str(r["provenance"]),
                                           uses={Use(k): Answer(v) for k, v in r["uses"].items()}, notes=str(r.get("notes", ""))))
                except (KeyError, ValueError, TypeError):
                    continue                                       # a blob that is not a rights record is not one
        out: dict[str, Rights] = {}
        for rights in sorted(declared, key=lambda r: r.recorded_on):    # a later declaration supersedes an earlier one
            out[rights.source_id] = rights
        out.update(REGISTRY)                                             # the code's records are never overridden
        return out

    def get_blob(self, kind: str, sha: str) -> dict:
        path = self.root / kind / f"{sha}.json"
        if not path.exists():
            raise NotArchived(f"{kind}/{sha} is not in the archive")
        text = path.read_text(encoding="utf-8")
        if hashlib.sha256(text.encode("utf-8")).hexdigest() != sha:
            raise RuntimeError(f"archive corruption: {kind}/{sha} does not hash to its name")
        return json.loads(text)

    def latest_entries(self) -> dict[str, dict]:
        """The most recent manifest entry per name; the manifest is read whole (it is a chain)."""
        out: dict[str, dict] = {}
        for e in self.entries():
            out[e["name"]] = e
        return out

    def latest_bars(self, names=None) -> dict[str, tuple[Bars, ActionSeries]]:
        """The most recently archived series per name — what a question reads.
        With ``names``, only those are read (M14.7: a survey box holds the
        manifest whole and the bars its grid needs, nothing else); a name
        with no entry is refused by name. Without, every series, strictly."""
        latest = self.latest_entries()
        if names is None:
            return {n: self.get(e["sha"]) for n, e in latest.items()}
        missing = sorted(set(names) - set(latest))
        if missing:
            raise NotArchived(f"not in the archive's manifest: {', '.join(missing)}")
        out: dict[str, tuple[Bars, ActionSeries]] = {}
        for n in sorted(set(names)):
            try:
                out[n] = self.get(latest[n]["sha"])
            except NotArchived as e:
                raise NotArchived(f"{n}: its latest series is named in the manifest but not held here — {e}") from e
        return out

    def bar_paths(self, names) -> list[Path]:
        """The files under ``bars/`` that hold the latest series of ``names`` — what a
        survey box needs beside the manifest (M14.7); a name with no entry is refused."""
        latest = self.latest_entries()
        missing = sorted(set(names) - set(latest))
        if missing:
            raise NotArchived(f"not in the archive's manifest: {', '.join(missing)}")
        return [self.root / "bars" / f"{latest[n]['sha']}.json" for n in sorted(set(names))]
