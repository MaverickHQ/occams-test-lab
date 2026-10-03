"""The Draft, the sandbox, the queue, and the Proposer base (M7.1-M7.4).

A Draft carries a mechanism, both interpretations, a falsifier and the
declared floor — and no standing. It is not a Hypothesis until a human
registers it, and the code path that registers requires ``Confirmation``
with ``human=True`` whenever alpha is spent (``occams.hypothesis.register``).
Nothing in this package imports that path.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, fields
from typing import Any, ClassVar
from urllib.parse import urlparse

from occams.config import InformationAxis
from occams.hypothesis import Gates, Hypothesis, PowerPlan, Tier
from occams.measurement import Floor
from occams.register import Store


class SandboxViolation(PermissionError):
    """A proposer reached for something it has no authority over."""


class DraftRefused(ValueError):
    """A draft that cannot become a Hypothesis, refused before it costs anything."""


@dataclass(frozen=True)
class Sweep:
    """The declared search space: ``search_space_size`` is its product."""

    axes: tuple[tuple[str, tuple[float, ...]], ...]

    def __post_init__(self):
        object.__setattr__(self, "axes", tuple((str(k), tuple(float(x) for x in v)) for k, v in self.axes))

    @property
    def size(self) -> int:
        return math.prod(len(v) for _, v in self.axes) if self.axes else 0

    def as_dict(self) -> dict[str, list[float]]:
        return {k: list(v) for k, v in self.axes}


@dataclass(frozen=True)
class Draft:
    proposer: str
    axis: InformationAxis
    mechanism: str
    if_true: str
    if_false: str
    falsifier: str
    floor: Floor
    sweep: Sweep
    sigma_r: float
    sigma_provenance: str
    power: float          # the plan's power target; alpha is the accountant's, never the proposer's (R4.4)
    gates: Gates
    tier: Tier = Tier.MECHANISM
    parent_id: str | None = None
    sources: tuple[str, ...] = ()    # references to retrieved content, never its text
    surfaced: tuple[str, ...] = ()   # quoted passages that read as instructions (M7.5)
    notes: str = ""

    @property
    def search_space_size(self) -> int:
        return self.sweep.size


def validate_draft(d: Draft) -> None:
    """M7.2: refused at zero alpha cost. Lists every defect."""
    if not isinstance(d, Draft):
        raise TypeError(f"a proposer's output is a Draft, not {type(d).__name__} — schema-validated (M7.4)")
    reasons = []
    for k in ("mechanism", "if_true", "if_false", "falsifier"):
        if not str(getattr(d, k, "")).strip():
            reasons.append(f"{k} is missing")
    if not isinstance(d.axis, InformationAxis):
        reasons.append("axis is not a closed-enum InformationAxis")
    if not isinstance(d.floor, Floor) or d.floor.ev_net_r <= 0 or d.floor.min_trades_per_year <= 0:
        reasons.append("floor must be a positive pair")
    if not isinstance(d.sweep, Sweep) or d.sweep.size < 1:
        reasons.append("sweep must declare at least one cell")
    if not (d.sigma_r > 0):
        reasons.append("sigma_r must be positive")
    if not str(d.sigma_provenance).strip():
        reasons.append("sigma_r needs provenance — an assumed sigma is how a power plan is rigged")
    if not (0 < d.power < 1):
        reasons.append("power must be in (0, 1)")
    if hasattr(d, "alpha"):
        reasons.append("a proposer may not set alpha (R4.4)")
    if not isinstance(d.gates, Gates):
        reasons.append("gates must be Gates")
    if d.tier is Tier.IMPLEMENTATION and not d.parent_id:
        reasons.append("an implementation draft names its mechanism parent")
    if reasons:
        raise DraftRefused("draft refused before it cost anything: " + "; ".join(reasons))


def to_hypothesis(d: Draft, *, id: str, available_n: int, alpha: float) -> Hypothesis:
    """A DRAFT-state Hypothesis. ``alpha`` is the accountant's per-question
    figure (``rate × search_space_size``, M6.4); registering is someone
    else's act."""
    validate_draft(d)
    return Hypothesis(id=id, tier=d.tier, axis=d.axis, mechanism=d.mechanism, if_true=d.if_true,
                      if_false=d.if_false, falsifier=d.falsifier, floor=d.floor,
                      power_plan=PowerPlan(d.sigma_r, alpha, d.power, available_n), gates=d.gates,
                      search_space_size=d.search_space_size, parent_id=d.parent_id)


# ---- the sandbox --------------------------------------------------------

class ReadOnlyRegister:
    """The Register as a proposer sees it: records, and nothing that writes."""

    def __init__(self, register):
        self._register = register

    def records(self) -> list[dict]:
        return self._register.records()

    def verify(self) -> int:
        return self._register.verify()

    def __getattr__(self, name: str):
        raise SandboxViolation(f"a proposer cannot {name} the Register; it emits drafts (D15)")


def _draft_record(cls):
    cls.__draft_record__ = True
    return cls


@_draft_record
@dataclass(frozen=True)
class DraftQueued:
    proposer: str
    axis: str
    tier: str
    mechanism: str
    if_true: str
    if_false: str
    falsifier: str
    floor_ev_net_r: float
    floor_min_trades_per_year: float
    sweep: dict
    search_space_size: int
    sigma_r: float
    sigma_provenance: str
    power: float
    gates: dict
    parent_id: str | None
    sources: tuple[str, ...]
    surfaced: tuple[str, ...]
    notes: str

    @classmethod
    def from_draft(cls, d: Draft) -> DraftQueued:
        return cls(d.proposer, d.axis.value, d.tier.value, d.mechanism, d.if_true, d.if_false, d.falsifier,
                   d.floor.ev_net_r, d.floor.min_trades_per_year, d.sweep.as_dict(), d.search_space_size,
                   d.sigma_r, d.sigma_provenance, d.power,
                   {f.name: getattr(d.gates, f.name) for f in fields(d.gates)}, d.parent_id,
                   tuple(d.sources), tuple(d.surfaced), d.notes)


class DraftQueue(Store):
    """Append-only, hash-chained like the Register; a human reads it."""

    marker: ClassVar[str] = "__draft_record__"
    name: ClassVar[str] = "Draft queue"

    def enqueue(self, d: Draft) -> dict:
        validate_draft(d)  # schema-validated output (M7.4); refused at zero alpha cost (M7.2)
        return self.append(DraftQueued.from_draft(d))

    def drafts(self) -> list[dict]:
        return self.records()


class WriteOnlyQueue:
    """The queue as a proposer sees it: enqueue, and nothing that reads."""

    def __init__(self, queue: DraftQueue):
        self._queue = queue

    def enqueue(self, d: Draft) -> dict:
        return self._queue.enqueue(d)

    def __getattr__(self, name: str):
        raise SandboxViolation(f"a proposer cannot {name} the draft queue; it writes drafts and reads none")


@dataclass(frozen=True)
class Allowlist:
    hosts: frozenset[str]

    def check(self, url: str) -> str:
        host = urlparse(url).hostname or ""
        if host not in self.hosts:
            raise SandboxViolation(f"{host!r} is not on the proposer's network allowlist {sorted(self.hosts)}")
        return host


class _Denied:
    def __init__(self, what: str):
        self._what = what

    def __getattr__(self, name: str):
        raise SandboxViolation(f"a proposer has no {self._what}")

    def __getitem__(self, key):
        raise SandboxViolation(f"a proposer has no {self._what}")

    def __bool__(self):
        raise SandboxViolation(f"a proposer has no {self._what}")


@dataclass
class Sandbox:
    """Everything a proposer may touch. Anything else raises."""

    register: ReadOnlyRegister
    queue: WriteOnlyQueue
    network: Allowlist
    fetcher: Any = None  # injected; tests never reach a socket
    credentials: Any = field(default_factory=lambda: _Denied("credentials"))
    operations: Any = field(default_factory=lambda: _Denied("Operations access"))

    @classmethod
    def build(cls, register, queue: DraftQueue, *, allow_hosts: frozenset[str] = frozenset(), fetcher=None) -> Sandbox:
        return cls(ReadOnlyRegister(register), WriteOnlyQueue(queue), Allowlist(frozenset(allow_hosts)), fetcher)

    def retrieve(self, url: str):
        """Allowlist first; then the injected fetcher; then quarantine (M7.5)."""
        from occams.proposers.content import Retrieved, quarantine

        self.network.check(url)
        if self.fetcher is None:
            raise SandboxViolation("no fetcher is configured for this sandbox")
        return quarantine(Retrieved(url, self.fetcher(url)))


class Proposer:
    """Emits Drafts. Holds nothing that spends — and is not an ABC, because
    ``ABCMeta`` would give every subclass a method called ``register``."""

    name: str = "proposer"

    def propose(self, sandbox: Sandbox, *args, **kwargs) -> tuple[Draft, ...]:
        raise NotImplementedError("a proposer implements propose()")
