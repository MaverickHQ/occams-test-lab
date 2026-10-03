"""Two append-only event stores, split on publishability (F8, ADR-0008).

**Register** — hypotheses, floors, verdicts in net R, refusals, alpha spend,
spec hashes, reserve looks. Publishable by construction: **no record type
that can be appended to it may carry account currency** (S7). That is
enforced when the record *class* is declared, by ``@register_record``, which
refuses a field typed ``Money`` or named like money — a type-level
assertion, not a review step.

**Operations** — orders, fills, money, position state. Never published.

Both are hash-chained JSONL: every line carries the previous line's digest,
so rewriting history fails ``verify()`` and ``append`` refuses to extend a
file whose tail no longer matches. The two are joined by spec hash.
"""

# M14.6: a package. The chain machinery is ``store.py``, the record types ``records.py``;
# this file binds them into the two stores and re-exports every name the module had.

from __future__ import annotations

from occams.register.records import (  # noqa: F401
    HypothesisRegistered,
    HypothesisMeasured,
    HypothesisResolved,
    PathsArchived,
    ClassifierFrozen,
    UniverseDeclared,
    CalendarFrozen,
    LabClosed,
    RefusalRecorded,
    StrategyTransitioned,
    ReserveLook,
    ForwardWindowOpened,
    ForwardWindowResolved,
    SurveyRecorded,
    EraDecomposition,
    Shrinkage,
    ProgrammeStopped,
    RollMeasured,
    OrderIntent,
    ProposalIssued,
    ForwardFill,
    Exposure,
)
from occams.register.store import (  # noqa: F401
    FORBIDDEN_IN_REGISTER,
    Money,
    NotPublishable,
    Store,
    TamperedHistory,
    _plain,
    canonical,
    now,
    operations_record,
    register_record,
)


class Register(Store):
    marker = "__register_record__"
    name = "Register"
    EraDecomposition = EraDecomposition
    Shrinkage = Shrinkage
    ProgrammeStopped = ProgrammeStopped
    RollMeasured = RollMeasured
    HypothesisRegistered = HypothesisRegistered
    HypothesisMeasured = HypothesisMeasured
    HypothesisResolved = HypothesisResolved
    RefusalRecorded = RefusalRecorded
    StrategyTransitioned = StrategyTransitioned
    ReserveLook = ReserveLook
    ForwardWindowOpened = ForwardWindowOpened
    ForwardWindowResolved = ForwardWindowResolved
    PathsArchived = PathsArchived
    LabClosed = LabClosed
    ClassifierFrozen = ClassifierFrozen
    CalendarFrozen = CalendarFrozen
    UniverseDeclared = UniverseDeclared
    SurveyRecorded = SurveyRecorded


class Operations(Store):
    marker = "__operations_record__"
    name = "Operations"
    OrderIntent = OrderIntent
    ProposalIssued = ProposalIssued
    ForwardFill = ForwardFill
    Exposure = Exposure

    def live_exposures(self, spec_hash: str | None = None) -> list[dict]:
        rows = [r for r in self.records() if r["type"] == "Exposure"]
        return [r for r in rows if spec_hash is None or r["spec_hash"] == spec_hash]


__all__ = [
    "CalendarFrozen",
    "ClassifierFrozen",
    "EraDecomposition",
    "Exposure",
    "FORBIDDEN_IN_REGISTER",
    "ForwardFill",
    "ForwardWindowOpened",
    "ForwardWindowResolved",
    "HypothesisMeasured",
    "HypothesisRegistered",
    "HypothesisResolved",
    "LabClosed",
    "Money",
    "NotPublishable",
    "Operations",
    "OrderIntent",
    "PathsArchived",
    "ProgrammeStopped",
    "ProposalIssued",
    "RefusalRecorded",
    "Register",
    "RollMeasured",
    "ReserveLook",
    "Shrinkage",
    "Store",
    "StrategyTransitioned",
    "SurveyRecorded",
    "TamperedHistory",
    "UniverseDeclared",
    "_plain",
    "canonical",
    "now",
    "operations_record",
    "register_record",
]
