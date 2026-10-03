"""``alpha_budget`` and ``search_budget`` — the accountant (M6.1-M6.10).

**Alpha** is declared: a total, a reserve, a budget per axis, and per-test
rates per runnable axis (R4.1-R4.3). Registration spends
``rate × search_space_size`` from the axis (R4.4); a proposer sets neither
number. Exhaustion refuses registration on that axis (R4.5); a zero axis
becomes viable only by a recorded transfer from reserve (ADR-0017);
replenishment accrues mechanically against observations no Hypothesis has
consumed (D14). The invariant ``sum(axis budgets) + reserve == total`` holds
on load and after every transfer (S8).

**Search** is what a Hypothesis consumed: a partition, its bounds, its
names. Overlap with a resolved Hypothesis on the same axis beyond the
declared threshold refuses registration until a ``supersedes`` link or a
stated distinction is supplied (R4.9, D16).

The accountant keeps no state of its own: balances are replayed from the
Register, so the ledger is exactly as trustworthy as the chain.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, replace
from pathlib import Path

from occams.config import Config, InformationAxis
from occams.guards import Refusal
from occams.hypothesis import Tier
from occams.register import Register, register_record

EXHAUSTED = "AXIS_BUDGET_EXHAUSTED"


# ---- Register records ----------------------------------------------------

@register_record
@dataclass(frozen=True)
class AlphaSpent:
    hypothesis_id: str
    axis: str
    tier: str
    rate: float
    search_space_size: int
    alpha_spent: float       # alpha, not money — S7 refuses the word "amount" here, correctly
    remaining_after: float
    config_sha: str


@register_record
@dataclass(frozen=True)
class ReserveTransfer:
    axis: str
    alpha_moved: float
    decision: str
    reserve_after: float


@register_record
@dataclass(frozen=True)
class AlphaAccrued:
    axis: str
    alpha_accrued: float
    new_observations: int
    base_observations: int


@register_record
@dataclass(frozen=True)
class ObservationsConsumed:
    hypothesis_id: str
    axis: str
    partition: str
    start_day: int
    end_day: int
    names: tuple[str, ...]


for _r in (AlphaSpent, ReserveTransfer, AlphaAccrued, ObservationsConsumed):
    setattr(Register, _r.__name__, _r)


# ---- the alpha budget -------------------------------------------------------

@dataclass(frozen=True)
class AxisState:
    declared: float
    mechanism_rate: float
    implementation_rate: float
    transferred_in: float = 0.0
    accrued: float = 0.0
    spent: float = 0.0

    @property
    def remaining(self) -> float:
        return self.declared + self.transferred_in + self.accrued - self.spent

    @property
    def runnable(self) -> bool:
        return self.remaining > 0 and self.mechanism_rate > 0


class AlphaBudget:
    """Balances replayed from config + the Register. Nothing is cached."""

    def __init__(self, cfg: Config, register: Register, *, config_sha: str):
        self.cfg = cfg
        self.register = register
        self.config_sha = config_sha
        self.total = cfg.alpha.total
        self.reserve = cfg.alpha.reserve
        self.axes: dict[InformationAxis, AxisState] = {
            ax: AxisState(a.budget, a.mechanism_test_alpha, a.implementation_test_alpha)
            for ax, a in cfg.alpha.axes.items()}
        self._replay()
        self.invariant()

    def _replay(self) -> None:
        for r in self.register.records():
            t = r["type"]
            if t == "AlphaSpent":
                ax = InformationAxis(r["axis"])
                self.axes[ax] = replace(self.axes[ax], spent=self.axes[ax].spent + r["alpha_spent"])
            elif t == "ReserveTransfer":
                ax = InformationAxis(r["axis"])
                self.reserve -= r["alpha_moved"]
                self.axes[ax] = replace(self.axes[ax], transferred_in=self.axes[ax].transferred_in + r["alpha_moved"])
            elif t == "AlphaAccrued":
                ax = InformationAxis(r["axis"])
                self.axes[ax] = replace(self.axes[ax], accrued=self.axes[ax].accrued + r["alpha_accrued"])

    def invariant(self) -> None:
        """S8, R4.7: declared axis budgets (plus transfers) and the reserve
        sum to the total, exactly. Accruals are new budget against new
        observations and sit outside the declared total by design (D14)."""
        s = sum(a.declared + a.transferred_in for a in self.axes.values()) + self.reserve
        if not math.isclose(s, self.total, rel_tol=0, abs_tol=1e-12):
            raise RuntimeError(f"S8 broken: axis budgets + reserve = {s} != total {self.total}")

    def rate(self, axis: InformationAxis, tier: Tier) -> float:
        a = self.axes[axis]
        return a.mechanism_rate if tier is Tier.MECHANISM else a.implementation_rate

    def spend_for(self, axis: InformationAxis, tier: Tier, search_space_size: int) -> float:
        """R4.4: the corrected spend, computed here and nowhere else."""
        return self.rate(axis, tier) * int(search_space_size)

    def plan_alpha(self, axis: InformationAxis, tier: Tier, search_space_size: int) -> float:
        """The per-question alpha a power plan carries: rate × k, so that the
        Bonferroni per-cell alpha is the configured rate."""
        return self.spend_for(axis, tier, search_space_size)

    def remaining(self, axis: InformationAxis) -> float:
        return self.axes[axis].remaining

    def check(self, axis: InformationAxis, tier: Tier, search_space_size: int) -> Refusal | None:
        a = self.axes[axis]
        if not a.runnable:
            return Refusal("DRAFT->REGISTERED", f"{EXHAUSTED}: axis {axis.value} cannot run — budget {a.remaining:.4g}, "
                                                 f"rate {a.mechanism_rate:.4g}; a zero axis becomes viable by a recorded transfer "
                                                 f"from reserve and configured rates (ADR-0017)", {"axis": axis.value})
        amount = self.spend_for(axis, tier, search_space_size)
        if amount > a.remaining + 1e-15:
            return Refusal("DRAFT->REGISTERED", f"{EXHAUSTED}: {tier.value} question of {search_space_size} cells needs "
                                                 f"{amount:.4g} alpha on {axis.value}; {a.remaining:.4g} remains — exhaustion is "
                                                 f"terminal until new data (ADR-0011)",
                           {"axis": axis.value, "needed": amount, "remaining": a.remaining})
        return None

    def charge(self, hypothesis_id: str, axis: InformationAxis, tier: Tier, search_space_size: int) -> float:
        r = self.check(axis, tier, search_space_size)
        if r is not None:
            raise RuntimeError(r.reason)  # callers check() first; this is the last line of defence
        amount = self.spend_for(axis, tier, search_space_size)
        a = self.axes[axis]
        self.axes[axis] = replace(a, spent=a.spent + amount)
        self.register.append(AlphaSpent(hypothesis_id, axis.value, tier.value, self.rate(axis, tier),
                                        int(search_space_size), amount, self.axes[axis].remaining, self.config_sha))
        return amount

    def transfer_from_reserve(self, axis: InformationAxis, amount: float, *, decision: str) -> None:
        """A recorded decision (R4.7). The invariant holds before and after."""
        if not decision.strip():
            raise ValueError("a reserve transfer records its decision")
        if amount <= 0 or amount > self.reserve + 1e-15:
            raise ValueError(f"cannot transfer {amount} from a reserve of {self.reserve}")
        self.reserve -= amount
        a = self.axes[axis]
        self.axes[axis] = replace(a, transferred_in=a.transferred_in + amount)
        self.invariant()
        self.register.append(ReserveTransfer(axis.value, amount, decision, self.reserve))

    def accrue(self, axis: InformationAxis, *, new_observations: int, base_observations: int) -> float:
        """D14: replenishment is a computation. New observations — days no
        Hypothesis has consumed because they did not exist — accrue budget
        in proportion to the declared budget per declared observation."""
        if new_observations <= 0 or base_observations <= 0:
            raise ValueError("accrual needs positive observation counts")
        amount = self.axes[axis].declared * new_observations / base_observations
        a = self.axes[axis]
        self.axes[axis] = replace(a, accrued=a.accrued + amount)
        self.register.append(AlphaAccrued(axis.value, amount, int(new_observations), int(base_observations)))
        return amount


# ---- the search budget ------------------------------------------------------

@dataclass(frozen=True)
class Consumed:
    """What a Hypothesis consumed: an axis, a partition and its bounds, the
    names it pooled over."""

    hypothesis_id: str
    axis: InformationAxis
    partition: str
    start_day: int
    end_day: int
    names: frozenset[str]


def overlap(new: Consumed, old: Consumed) -> float:
    """Fraction of ``new``'s (name, day) observations that ``old`` consumed."""
    if new.axis is not old.axis or new.partition != old.partition:
        return 0.0
    days_new = max(0, new.end_day - new.start_day)
    if days_new == 0 or not new.names:
        return 0.0
    days_shared = max(0, min(new.end_day, old.end_day) - max(new.start_day, old.start_day))
    names_shared = len(new.names & old.names)
    return (days_shared * names_shared) / (days_new * len(new.names))


class SearchBudget:
    def __init__(self, register: Register):
        self.register = register

    def consumed(self) -> list[Consumed]:
        return [Consumed(r["hypothesis_id"], InformationAxis(r["axis"]), r["partition"], r["start_day"], r["end_day"],
                         frozenset(r["names"])) for r in self.register.records() if r["type"] == "ObservationsConsumed"]

    def record(self, c: Consumed) -> None:
        self.register.append(ObservationsConsumed(c.hypothesis_id, c.axis.value, c.partition, c.start_day, c.end_day,
                                                  tuple(sorted(c.names))))

    def gate(self, new: Consumed, *, threshold: float, supersedes: str | None, distinction: str | None) -> Refusal | None:
        """R4.9 / D16: overlap beyond the threshold refuses until a
        supersedes link or a stated distinction is supplied."""
        for old in self.consumed():
            f = overlap(new, old)
            if f > threshold:
                if supersedes == old.hypothesis_id or (distinction or "").strip():
                    continue
                return Refusal("DRAFT->REGISTERED", f"consumed-observation overlap {f:.0%} with {old.hypothesis_id} exceeds "
                                                     f"the declared threshold {threshold:.0%}; supply a supersedes link or a "
                                                     f"stated distinction (R4.9)",
                               {"overlaps": old.hypothesis_id, "fraction": f, "threshold": threshold})
        return None


# ---- M6.10: the donor register as a known answer -----------------------------

def donor_replay(path: Path) -> tuple[float, float]:
    """Raw spend = Σ alpha_allocated; corrected = Σ alpha_allocated ×
    search_space_size. The donor's 24 hypotheses give 0.620 and 1.700 — a
    corrected spend above 1, which this budget forbids."""
    d = json.loads(Path(path).read_text(encoding="utf-8"))
    hs = d["hypotheses"]
    raw = sum(float(h.get("alpha_allocated") or 0.0) for h in hs)
    corrected = sum(float(h.get("alpha_allocated") or 0.0) * int(h.get("search_space_size") or 1) for h in hs)
    return round(raw, 6), round(corrected, 6)
