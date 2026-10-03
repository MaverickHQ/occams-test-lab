"""What the console knows, and where each fact came from (M11.4, F8).

Three sources and no others. **The Register**, chain-verified first: a
tampered Register is a failure, not a report. **The archive manifest**,
never the bars: names, spans, counts and content hashes, so no vendor data
can reach the page. **The controls**, recomputed at build through the same
pipeline `make null` and `make signal` use, because a reader has no reason
to trust a finding until the instrument has shown it can refuse a dead
world and accept a planted edge.

The author's configuration reaches this module only as an ``AuthorView``:
the alpha split, the lab falsifier and the partition split. It has no field
for money, so money cannot be rendered by construction rather than by
review (S7, R9). Without it the page is the *plain build* and shows spend
only; with it, balances too, and says so.
"""

from __future__ import annotations

import subprocess
import tempfile
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from occams.register import Register

CALENDAR_FLOOR = 600_000   # an archive day below this is a bar index, not a calendar ordinal (pre ADR-0005 fix)
PAST_MEASURED = ("FORWARD", "APPROVED", "LIVE", "RETIRED")


@dataclass(frozen=True)
class AuthorView:
    """The three things a build with the author's configuration may show.
    Built from a ``Config`` by the command line; nothing else is copied."""

    axis_budgets: dict[str, float]
    reserve: float
    total: float
    falsifier_count: int
    falsifier_outcome: str
    overlap_threshold: float
    partitions: tuple[float, float, float]
    config_sha: str

    @classmethod
    def from_config(cls, cfg) -> "AuthorView":
        from occams.whatif import config_sha

        return cls({ax.value: float(a.budget) for ax, a in cfg.alpha.axes.items()},
                   float(cfg.alpha.reserve), float(cfg.alpha.total),
                   int(cfg.lab.falsifier_count), str(cfg.lab.falsifier_outcome), float(cfg.lab.overlap_threshold),
                   (float(cfg.partitions.definition), float(cfg.partitions.measurement), float(cfg.partitions.reserve)),
                   config_sha(cfg))


@dataclass(frozen=True)
class Finding:
    """One registered question with everything the Register later said about it."""

    registered: dict
    spent: dict | None
    consumed: list[dict]
    measured: dict | None
    resolved: dict | None
    paths: dict | None
    refusals: list[dict]
    transitions: list[dict]
    depth: dict | None = None        # EraDecomposition (M12.6): the winner's eras, each held out, and its missed entries
    shrinkage: dict | None = None    # Shrinkage (M12.6): the survey cell's definition numbers beside the measured ones

    @property
    def id(self) -> str:
        return self.registered["hypothesis_id"]

    REFUSED_AT_MEASUREMENT = "registered, refused at measurement, unresolved"

    @property
    def state(self) -> str:
        if self.resolved:
            return self.resolved["outcome"]
        if self.measured:
            return "measured"
        if any(r.get("transition") == "REGISTERED->MEASURED" for r in self.refusals):
            return self.REFUSED_AT_MEASUREMENT      # M14.5: alpha spent, no verdict, the loop repeats the refusal; the author's
        return "registered"


@dataclass(frozen=True)
class Series:
    name: str
    bars: int
    first_day: int
    last_day: int
    first_at: str
    last_at: str
    actions: int
    source_id: str
    sha: str
    requested_start: str | None
    requested_end: str | None

    @property
    def calendar(self) -> bool:
        return self.first_day >= CALENDAR_FLOOR


@dataclass(frozen=True)
class Facts:
    register_path: str
    head: str
    chain: list[dict]
    generated: str
    repo_sha: str | None
    engine_sha: str | None
    config_sha: str | None
    author: AuthorView | None
    controls: list
    controls_ok: bool
    findings: list[Finding]
    series: list[Series]
    archive_present: bool
    classifier: dict | None
    lab_closed: dict | None
    spent_by_axis: dict[str, float] = field(default_factory=dict)
    surveys: list[dict] = field(default_factory=list)   # SurveyRecorded payloads (M12.4)
    stopped: dict | None = None                          # ProgrammeStopped (M12.8): alpha exhausted or the author's stop

    @property
    def records(self) -> list[dict]:
        return [line["payload"] for line in self.chain]

    def of(self, type_: str) -> list[dict]:
        return [p for p in self.records if p["type"] == type_]

    @property
    def resolved(self) -> list[dict]:
        return [f.resolved for f in self.findings if f.resolved]

    def falsifier_standing(self) -> int:
        """Resolved *mechanism* verdicts with the falsifier's outcome (null unless the author says otherwise)."""
        outcome = self.author.falsifier_outcome if self.author else "null"
        return sum(1 for f in self.findings
                   if f.resolved and f.resolved["outcome"] == outcome and f.registered["tier"] == "mechanism")

    def strategies_past_measured(self) -> int:
        return len({t["spec_hash"] for t in self.of("StrategyTransitioned") if t["to_state"] in PAST_MEASURED})

    def bands(self) -> dict[str, tuple[int, int]]:
        """Partition bands on the archive's calendar. From the frozen calendar
        record when one exists (ADR-0038); else from the author's split over
        the common span; else from the Register's own cuts: the definition
        the classifier was frozen on, the measurement the questions consumed."""
        frozen = self.of("CalendarFrozen")
        if frozen:   # ADR-0038: the record carries the span and the split, so even a plain build draws the bands
            from occams.data.partitions import Partitions

            c = frozen[-1]
            return Partitions(*c["split"]).bounds_over(int(c["start_day"]), int(c["end_day"]))
        cal = [s for s in self.series if s.calendar]
        if self.author and cal:
            from occams.data.partitions import Partitions

            lo, hi = min(s.first_day for s in cal), max(s.last_day for s in cal)
            return Partitions(*self.author.partitions).bounds_over(lo, hi)
        out: dict[str, tuple[int, int]] = {}
        if self.classifier and self.classifier["definition_start_day"] >= CALENDAR_FLOOR:
            out["definition"] = (self.classifier["definition_start_day"], self.classifier["definition_end_day"])
        consumed = [c for c in self.of("ObservationsConsumed") if c["partition"] == "measurement"]
        if consumed:
            out["measurement"] = (min(c["start_day"] for c in consumed), max(c["end_day"] for c in consumed))
        if cal and "measurement" in out:
            out["reserve"] = (out["measurement"][1], max(s.last_day for s in cal) + 1)
        return out


# ---- gathering -------------------------------------------------------------------

def _repo_sha(near: Path) -> str | None:
    try:
        out = subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], cwd=str(near), capture_output=True,
                             text=True, timeout=5, check=False)
        return out.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def _series(archive_dir: Path | None) -> tuple[list[Series], bool]:
    if archive_dir is None or not (Path(archive_dir) / "manifest.jsonl").exists():
        return [], False
    from occams.data.archive import BarArchive

    latest: dict[str, dict] = {}
    for e in BarArchive(Path(archive_dir)).entries():
        if e.get("type") == "Archived":
            latest[e["name"]] = e     # the last manifest line per name is what a question reads
    out = [Series(e["name"], int(e["bars"]), int(e["first_day"]), int(e["last_day"]), e["first_at"], e["last_at"],
                  int(e.get("actions", 0)), e.get("source_id", ""), e["sha"], e.get("requested_start"), e.get("requested_end"))
           for e in latest.values()]
    return sorted(out, key=lambda s: s.name), True


def run_controls(which: str) -> list:
    """``which`` is ``all`` (both engines), ``synthetic`` (the fast one) or
    ``none``. Each control runs in its own temporary Register, as the make
    targets do; nothing is written anywhere that lasts."""
    if which == "none":
        return []
    from occams.controls import load_controls, run

    cfg = load_controls()
    engines = ("synthetic", "day_boxed") if which == "all" else ("synthetic",)
    return [run(kind, cfg, Path(tempfile.mkdtemp(prefix="occams-console-controls-")), engine=eng)
            for kind in ("null", "signal") for eng in engines]


def controls_hold(outcomes: list) -> bool:
    """S3 and S10: every null refused, every signal accepted."""
    return all((not o.accepted) if o.kind.startswith("null") else o.accepted for o in outcomes)


def _findings(records: list[dict]) -> list[Finding]:
    by: dict[str, dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for r in records:
        hid = r.get("hypothesis_id")
        if hid:
            by[hid][r["type"]].append(r)
    out = []
    for r in records:
        if r["type"] != "HypothesisRegistered":
            continue
        g = by[r["hypothesis_id"]]
        out.append(Finding(r, (g["AlphaSpent"] or [None])[-1], list(g["ObservationsConsumed"]),
                           (g["HypothesisMeasured"] or [None])[-1], (g["HypothesisResolved"] or [None])[-1],
                           (g["PathsArchived"] or [None])[-1], list(g["RefusalRecorded"]), list(g["StrategyTransitioned"]),
                           (g["EraDecomposition"] or [None])[-1], (g["Shrinkage"] or [None])[-1]))
    return out


def gather(register_path: Path, *, archive_dir: Path | None = None, author: AuthorView | None = None,
           controls: str = "all", generated: str | None = None, repo_sha: str | None = None,
           controls_outcomes: list | None = None) -> Facts:
    """Read, verify, recompute. Raises ``TamperedHistory`` on a broken chain.
    ``controls_outcomes`` lets a second programme reuse the controls the
    first already ran: one instrument, one calibration per build."""
    reg = Register(Path(register_path))
    chain = reg.chain()
    records = [line["payload"] for line in chain]
    measured = [r for r in records if r["type"] == "HypothesisMeasured"]
    frozen = [r for r in records if r["type"] == "ClassifierFrozen"]
    closed = [r for r in records if r["type"] == "LabClosed"]
    stopped = [r for r in records if r["type"] == "ProgrammeStopped"]
    stamped = [r["config_sha"] for r in records if r.get("config_sha")]
    spent: dict[str, float] = defaultdict(float)
    for r in records:
        if r["type"] == "AlphaSpent":
            spent[r["axis"]] += float(r["alpha_spent"])
    series, present = _series(archive_dir)
    outcomes = list(controls_outcomes) if controls_outcomes is not None else run_controls(controls)
    return Facts(
        register_path=str(register_path),
        head=chain[-1]["sha"] if chain else "genesis",
        chain=chain,
        generated=generated or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        repo_sha=repo_sha if repo_sha is not None else _repo_sha(Path(register_path).resolve().parent),
        engine_sha=measured[-1]["engine_sha"] if measured else None,
        config_sha=author.config_sha if author else (stamped[-1] if stamped else None),
        author=author,
        controls=outcomes,
        controls_ok=controls_hold(outcomes),
        findings=_findings(records),
        series=series,
        archive_present=present,
        classifier=frozen[-1] if frozen else None,
        lab_closed=closed[-1] if closed else None,
        spent_by_axis=dict(spent),
        surveys=[r for r in records if r["type"] == "SurveyRecorded"],
        stopped=stopped[-1] if stopped else None,
    )
