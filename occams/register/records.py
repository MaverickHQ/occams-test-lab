"""The record types the two stores accept (M14.6, split from ``occams/register.py``):
seventeen for the Register — publishable by construction, ``@register_record`` refusing any
field that could carry money — and four for Operations, never published. A record's
``type`` in the chain is its class name, unchanged by the move.
"""

from __future__ import annotations

from dataclasses import dataclass

from occams.register.store import Money, operations_record, register_record  # noqa: F401 — Money for the type check


# ---- Register record types (publishable by construction) ----------------

@register_record
@dataclass(frozen=True)
class HypothesisRegistered:
    hypothesis_id: str
    tier: str
    axis: str
    mechanism: str
    falsifier: str
    floor_ev_net_r: float
    floor_min_trades_per_year: float
    search_space_size: int
    required_n: int
    available_n: int
    alpha_spent: float
    registered_by: str
    parent_id: str | None
    supersedes: str | None
    config_sha: str = ""      # the config this registration ran under (M6.2)
    capability: bool = False  # a capability question registers at alpha 0 (R4.6)
    # M12.5 (N6): a question registered from a survey names it — every cell screened is counted beside it
    screened_cells: int = 0
    survey_results_sha: str = ""
    survey_cell: str = ""
    universe: str = ""

    @classmethod
    def from_hypothesis(cls, h) -> "HypothesisRegistered":
        sv = h.survey or {}
        return cls(h.id, h.tier.value, h.axis.value, h.mechanism, h.falsifier,
                   h.floor.ev_net_r, h.floor.min_trades_per_year, h.search_space_size,
                   h.required_n, h.power_plan.available_n, float(h.alpha_spent or 0.0),
                   h.registered_by or "", h.parent_id, h.supersedes, h.config_sha or "", bool(h.capability),
                   int(sv.get("screened_cells", 0)), str(sv.get("results_sha", "")), str(sv.get("cell", "")),
                   str(sv.get("universe", "")))


@register_record
@dataclass(frozen=True)
class HypothesisMeasured:
    hypothesis_id: str
    spec_hash: str
    engine: str
    engine_sha: str
    seed: int
    partition: str
    n: int
    search_space_size: int


@register_record
@dataclass(frozen=True)
class HypothesisResolved:
    hypothesis_id: str
    outcome: str
    ev_net_r: float
    trades_per_year: float
    spec_hash: str
    engine_sha: str
    seed: int
    partition: str
    refusals: tuple[str, ...]
    cost_basis: str = "unknown"
    family_hash: str = ""
    winner_cell: tuple[int, ...] = ()
    checks: tuple[str, ...] = ()    # ADR-0043: the checks this verdict was evaluated against, by name; empty means the four of DESIGN §3 as first written
    surface: str = ""               # ADR-0045: "margin" over always-long chose the winner, or "ev"; empty on records before the rule

    @classmethod
    def from_verdict(cls, hid: str, v) -> "HypothesisResolved":
        return cls(hid, v.outcome, v.ev_net_r, v.trades_per_year, v.spec_hash,
                   v.engine_sha, v.seed, v.partition, tuple(v.refusals), getattr(v, "cost_basis", "unknown"),
                   getattr(v, "family_hash", ""), tuple(getattr(v, "winner_cell", ())), tuple(getattr(v, "checks", ())),
                   str(getattr(v, "surface", "") or ""))


@register_record
@dataclass(frozen=True)
class PathsArchived:
    """The Monte Carlo path distribution behind a Verdict, by content hash (D19, M8.5)."""

    hypothesis_id: str
    spec_hash: str
    sha: str
    draws: int
    trades: int


@register_record
@dataclass(frozen=True)
class ClassifierFrozen:
    """The regime classifier, committed in its own registration before any
    strategy question exists (ADR-0005, D13, M7.6)."""

    frozen_hash: str
    short: int
    long: int
    band: float
    level: str
    index_name: str
    definition_start_day: int
    definition_end_day: int
    definition_first_at: str
    definition_last_at: str
    names: tuple[str, ...]
    persistence: float
    shares: dict
    seed: int
    config_sha: str
    supersedes: str = ""
    reason: str = ""


@register_record
@dataclass(frozen=True)
class UniverseDeclared:
    """A named instrument set of the M0.7 class (M12.1): its members, the
    rule that chose them, when, from what source, and the bias that rule
    carries — named, never hidden. A survey cell names its universe by
    this record; the universe's calendar is frozen under its name."""

    name: str
    members: tuple[str, ...]
    instrument_class: str
    source_id: str
    rule: str
    chosen_on: str
    bias: str
    notes: str = ""


@register_record
@dataclass(frozen=True)
class CalendarFrozen:
    """The common span every partition is cut from (ADR-0038, amending
    ADR-0006). Written once by the author's act; bars beyond ``end_day``
    are forward data and fall in no partition. A second freeze is a
    recorded supersession, never a re-run."""

    start_day: int
    end_day: int
    definition_end_day: int
    measurement_end_day: int
    split: tuple[float, float, float]
    names: tuple[str, ...]
    config_sha: str
    reason: str = ""
    supersedes: str = ""
    universe: str = ""     # M12.1: the universe this calendar is cut for; "" is the Register-wide calendar


@register_record
@dataclass(frozen=True)
class LabClosed:
    """The lab's own falsifier fired (ADR-0033)."""

    falsifier_count: int
    outcome: str
    verdicts: tuple[str, ...]


@register_record
@dataclass(frozen=True)
class RefusalRecorded:
    transition: str
    reason: str
    evidence: dict
    spec_hash: str | None
    hypothesis_id: str | None


@register_record
@dataclass(frozen=True)
class StrategyTransitioned:
    spec_hash: str
    from_state: str
    to_state: str
    hypothesis_id: str | None


@register_record
@dataclass(frozen=True)
class ReserveLook:
    spec_hash: str
    hypothesis_id: str


@register_record
@dataclass(frozen=True)
class ForwardWindowOpened:
    spec_hash: str
    hypothesis_id: str | None
    min_trades: int
    max_duration_days: int
    opened_at: str
    venue_kind: str


@register_record
@dataclass(frozen=True)
class ForwardWindowResolved:
    spec_hash: str
    hypothesis_id: str | None
    outcome: str
    statement: str
    trades: int
    days_elapsed: int
    defects: tuple[str, ...]


@register_record
@dataclass(frozen=True)
class SurveyRecorded:
    """A survey ran a committed grid on the definition partition only, at
    zero alpha (M12.3). Nothing in it is a verdict; every cell screened is
    counted beside every question later registered from it (N6)."""

    grid_name: str
    grid_sha: str
    results_sha: str
    cell_count: int
    universes: tuple[str, ...]
    calendars: tuple[tuple[str, int, int], ...]   # (universe, definition start day, definition end day)
    classifier_hash: str
    engine_shas: dict
    seed: int
    out_dir: str
    reason: str = ""


@register_record
@dataclass(frozen=True)
class EraDecomposition:
    """The winner cell's trades on the measurement partition, split into
    eras of equal span, with each era held out and the entries the fill
    auditor refused (M12.6, ADR-0041). A recorded diagnostic, not a gate:
    it becomes one only if the author declares it."""

    hypothesis_id: str
    spec_hash: str
    partition: str
    eras: tuple[dict, ...]                   # {"bounds": [lo, hi), "n": int, "ev_net": float | None}
    leave_one_era_out: tuple[float | None, ...]
    missed: int
    missed_by_name: dict
    seed: int


@register_record
@dataclass(frozen=True)
class Shrinkage:
    """A question registered from a survey, measured: the cell's definition
    numbers beside the measured ones at the same geometry against
    always-long (M12.6, N6). Screening selects; this records by how much."""

    hypothesis_id: str
    survey_results_sha: str
    survey_cell: str
    screened_cells: int
    definition_trades: int
    definition_ev_net: float | None
    definition_margin_net: float | None
    measured_trades: int
    measured_ev_net: float
    measured_baseline_ev_net: float | None
    measured_margin_net: float | None
    ev_shrinkage: float | None               # measured − definition, net R per trade
    margin_shrinkage: float | None


@register_record
@dataclass(frozen=True)
class RollMeasured:
    """M15.9: a resolved question re-measured on a moving cut of its own
    measurement partition — the window's start rolled forward, its end
    fixed, the reserve never touched — in a rolls Register beside the
    programme's, which a stopped programme never writes again. A roll is a
    record and never a verdict."""

    hypothesis_id: str
    roll: int
    rolls: int
    window_start_day: int
    window_end_day: int
    measurement_start_day: int       # the partition the question was resolved on: the roll lies inside it
    measurement_end_day: int
    n: int
    powered: bool                    # the window still holds the trades the power plan required (M8.2); a roll may not
    winner_spec_hash: str
    ev_net_r: float
    margin_net_r: float | None
    refused_by: tuple[str, ...]
    surface: str
    seed: int
    source_register: str             # the programme's Register the question is resolved in, by file name
    source_head: str                 # that Register's head sha when the roll ran
    engine_sha: str


@register_record
@dataclass(frozen=True)
class ProgrammeStopped:
    """A programme stopped by a condition other than its falsifier (M12.8):
    its alpha is exhausted — no runnable axis can afford the smallest
    question the gates would let register — or the author stopped it, with
    the reason. Either is the author's act at ``programme stop … --yes``;
    the falsifier's own stop is ``LabClosed`` (ADR-0033). After any of the
    three nothing prepares, registers, surveys or measures in this
    Register, and the conclusion is written from it — after, not before."""

    kind: str                          # "alpha_exhausted" | "author"
    by: str
    reason: str
    alpha_remaining: dict              # axis -> alpha remaining at the stop (alpha, never money)
    smallest_charge: dict              # axis -> rate × plateau cells: the least a mechanism question there could cost
    verdicts: tuple[str, ...]          # resolved mechanism verdicts at the stop, in order
    surveys: int
    questions: int
    config_sha: str


# ---- Operations record types (never published) --------------------------

@operations_record
@dataclass(frozen=True)
class OrderIntent:
    spec_hash: str
    instrument: str
    side: str
    quantity: float
    risk: Money


@operations_record
@dataclass(frozen=True)
class ProposalIssued:
    spec_hash: str
    card_id: str
    instrument: str
    side: str
    quantity: float
    size: Money


@operations_record
@dataclass(frozen=True)
class ForwardFill:
    spec_hash: str
    card_id: str
    instrument: str
    fill_price: float
    quantity: float
    size: Money
    acknowledged_by: str
    acknowledged_at: str


@operations_record
@dataclass(frozen=True)
class Exposure:
    """A live position at minimum size, against the portfolio envelope (M10.2)."""

    spec_hash: str
    instrument: str
    quantity: float
    risk: Money
    opened_at: str
