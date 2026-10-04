"""The Hypothesis aggregate — a question about the world that resolves once
and costs alpha (ADR-0001), in two tiers (ADR-0027).

States: ``DRAFT -> REGISTERED -> MEASURED -> RESOLVED``. Every arrow is a
guard (F0) in ``occams/guards/``; a guard's refusal is recorded in the
Register and raised as ``Refused`` — never returned as ``None`` and never
swallowed.

Instances are frozen. A transition returns a new instance; the old one is
still what it was, which is what "append, never overwrite" means for
objects.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, replace

from occams.config import InformationAxis
from occams.core import power as _power
from occams.measurement import Floor, Measurement


class Tier(enum.Enum):
    MECHANISM = "mechanism"
    IMPLEMENTATION = "implementation"


class HypothesisState(enum.Enum):
    DRAFT = "DRAFT"
    REGISTERED = "REGISTERED"
    MEASURED = "MEASURED"
    RESOLVED = "RESOLVED"


@dataclass(frozen=True)
class PowerPlan:
    """Declared before running (R3). ``available_n`` is the trades the
    measurement partition holds; ``required_n`` is computed, never typed."""

    sigma_r: float
    alpha: float
    power: float
    available_n: int
    rho: float | None = None            # measured intra-cluster correlation, once it is (M7.7)
    rho_provenance: str = ""

    def with_clustering(self, cm) -> PowerPlan:
        """Consume a *measured* clustering: the design effect is applied to
        THIS plan's ``available_n`` (the trades the measurement partition
        affords), not to the sample the correlation was measured on. A bare
        number is refused — rho is measured, never asserted."""
        from occams.core import power as _p
        from occams.proposers.clustering import ClusterMeasurement

        if not isinstance(cm, ClusterMeasurement):
            raise TypeError("rho is measured, not asserted: pass a ClusterMeasurement from measure_clustering")
        # Kish's design effect with the MEAN cluster size, which is fractional
        # for a sparse signal (1.28 trades per index-day on the M0.7 class).
        # The vendored `power.effective_n` takes an integer cluster size; rounding
        # 1.28 to 1 returned the plan's N untouched and silently erased a 12%
        # correction at rho 0.43. Same formula, real m-bar.
        m = max(1.0, float(cm.cluster_size))
        rho = min(max(0.0, cm.rho), 0.999)
        deff = 1.0 + (m - 1.0) * rho
        eff = max(int(self.available_n / deff), 1) if deff > 1.0 else self.available_n
        assert eff == _p.effective_n(self.available_n, cluster_size=int(m), intra_r=rho) or m != int(m)
        return replace(self, available_n=eff, rho=cm.rho, rho_provenance=cm.provenance)

    def required_n(self, floor: Floor, search_space_size: int) -> int:
        """``((z_a + z_b) * sigma / effect)^2`` at Bonferroni-corrected alpha —
        the M0.15 formula, evaluated by the vendored calculator."""
        return _power.n_for_mean_shift(floor.ev_net_r / self.sigma_r,
                                       alpha=self.alpha / search_space_size,
                                       power=self.power)


@dataclass(frozen=True)
class Gates:
    """The MEASURED -> FORWARD thresholds, declared per Hypothesis (DESIGN §3)."""

    plateau_cells: int
    plateau_slack: float
    loo_min_fraction: float
    # ADR-0051: the slack in the winner's own standard errors. Declared at registration, with no default; ``None`` only on a
    # question registered before the rule, for which that half of the plateau check is absent
    plateau_slack_se: float | None = None


@dataclass(frozen=True)
class Confirmation:
    """Who confirmed a registration. Spending alpha needs a human (R4.8);
    an apparatus test at alpha 0 (ADR-0029) may confirm itself."""

    by: str
    human: bool


@dataclass(frozen=True)
class Verdict:
    """One-time resolution against the floor declared beforehand. Null is a
    result."""

    outcome: str  # "supported" | "null"
    ev_net_r: float
    trades_per_year: float
    spec_hash: str
    engine_sha: str
    seed: int
    partition: str
    refusals: tuple[str, ...]
    cost_basis: str = "unknown"  # a verdict that does not say is refused at approval (D23)
    family_hash: str = ""        # the template's hash: what was searched (ADR-0036)
    winner_cell: tuple[int, ...] = ()
    checks: tuple[str, ...] = ()  # the checks evaluated, by name (ADR-0043): the record says five, or which four
    surface: str = ""             # what chose the winner (ADR-0045): "margin" over always-long, or "ev"; "" on records before it
    engine_code_sha: str = ""     # the content hash of what measured it (ADR-0055); "" on verdicts before the rule


@dataclass(frozen=True)
class Hypothesis:
    id: str
    tier: Tier
    axis: InformationAxis
    mechanism: str
    if_true: str
    if_false: str
    falsifier: str
    floor: Floor
    power_plan: PowerPlan
    gates: Gates
    search_space_size: int
    parent_id: str | None = None
    supersedes: str | None = None
    capability: bool = False          # a capability question, not a market one: alpha 0 (R4.6)
    distinction: str | None = None    # the stated difference from an overlapping resolved question (R4.9)
    state: HypothesisState = HypothesisState.DRAFT
    registered_by: str | None = None
    alpha_spent: float | None = None
    config_sha: str | None = None
    spec_hash: str | None = None
    verdict: Verdict | None = None
    consumed: object = None           # a ledger.Consumed once measured (M6.6)
    survey: dict | None = None        # M12.5: the survey a question came from — results sha, cell, screened cells (N6), universe

    @property
    def required_n(self) -> int:
        return self.power_plan.required_n(self.floor, self.search_space_size)


def _advance(h: Hypothesis, to: HypothesisState, **changes) -> Hypothesis:
    return replace(h, state=to, **changes)


def register(h: Hypothesis, *, confirmation: Confirmation, parent: Hypothesis | None, register,
             budget=None, declared=None) -> Hypothesis:
    """DRAFT -> REGISTERED. The accountant computes and charges the spend —
    ``rate × search_space_size`` from the axis (R4.4) — and a proposer sets
    neither number. A capability question registers at alpha 0 (R4.6) and
    needs no accountant; a market question without one is refused.
    ``declared`` is the observation set the question intends to consume,
    for the overlap gate (R4.9)."""
    from occams.guards import Refusal
    from occams.guards import register as guard
    from occams.guards import refuse_or_pass

    closed = [r for r in register.records() if r["type"] == "LabClosed"]
    if closed:   # ADR-0033: terminal — enforced by the Register, not by memory
        c = closed[-1]
        refuse_or_pass(Refusal("DRAFT->REGISTERED", f"the lab is closed (ADR-0033): its falsifier fired on {c['falsifier_count']} "
                                                    f"{c['outcome']} mechanism verdicts ({', '.join(c['verdicts'])}); nothing registers "
                                                    f"after that record — a new question is a new programme",
                               {"falsifier_count": c["falsifier_count"], "verdicts": list(c["verdicts"])}),
                       register, spec_hash=None, hypothesis_id=h.id)
    stopped = [r for r in register.records() if r["type"] == "ProgrammeStopped"]
    if stopped:   # M12.8: a stopped programme registers nothing more — the same terminal rule, the other two conditions
        s = stopped[-1]
        how = "its alpha is exhausted" if s["kind"] == "alpha_exhausted" else "the author stopped it"
        refuse_or_pass(Refusal("DRAFT->REGISTERED", f"the programme is stopped (M12.8): {how} — {s['reason']} (recorded by {s['by']}); "
                                                    f"nothing registers after that record — a new question is a new programme",
                               {"kind": s["kind"], "by": s["by"]}),
                       register, spec_hash=None, hypothesis_id=h.id)
    refuse_or_pass(guard.check(h, confirmation=confirmation, parent=parent, budget=budget, declared=declared),
                   register, spec_hash=None, hypothesis_id=h.id)
    if h.capability or budget is None:
        spent, sha = 0.0, None
    else:
        spent = budget.charge(h.id, h.axis, h.tier, h.search_space_size)
        sha = budget.config_sha
    out = _advance(h, HypothesisState.REGISTERED, registered_by=confirmation.by, alpha_spent=spent, config_sha=sha)
    register.append(register.HypothesisRegistered.from_hypothesis(out))
    return out


def measure(h: Hypothesis, m: Measurement, *, register) -> Hypothesis:
    """REGISTERED -> MEASURED. Refused if underpowered (M8.2): the partition
    must hold at least ``required_n`` trades, and the measurement must show
    them."""
    from occams.guards import measure as guard
    from occams.guards import refuse_or_pass

    refuse_or_pass(guard.check(h, m), register, spec_hash=m.spec_hash, hypothesis_id=h.id)
    consumed = None
    if not h.capability:
        from occams.ledger.alpha_budget import Consumed, SearchBudget

        lo, hi = m.partition_bounds if m.partition_bounds else (min(t.day for c in m.cells for t in c.trades),
                                                                 max(t.day for c in m.cells for t in c.trades) + 1)
        consumed = Consumed(h.id, h.axis, m.partition, lo, hi, frozenset(m.winner.groups))
        SearchBudget(register).record(consumed)  # M6.6: exactly what it consumed
    out = _advance(h, HypothesisState.MEASURED, spec_hash=m.spec_hash, consumed=consumed)
    register.append(register.HypothesisMeasured(hypothesis_id=h.id, spec_hash=m.spec_hash,
                                                engine=m.engine, engine_sha=m.engine_sha,
                                                seed=m.seed, partition=m.partition,
                                                n=m.winner.n, search_space_size=m.search_space_size,
                                                engine_code_sha=str(getattr(m, "engine_code_sha", "") or "")))
    return out


def resolve(h: Hypothesis, v: Verdict, *, register) -> Hypothesis:
    """MEASURED -> RESOLVED. The spec hash is frozen into the Verdict (D2)."""
    from occams.guards import resolve as guard
    from occams.guards import refuse_or_pass

    refuse_or_pass(guard.check(h, v), register, spec_hash=v.spec_hash, hypothesis_id=h.id)
    out = _advance(h, HypothesisState.RESOLVED, verdict=v, spec_hash=v.spec_hash)
    register.append(register.HypothesisResolved.from_verdict(h.id, v))
    return out
