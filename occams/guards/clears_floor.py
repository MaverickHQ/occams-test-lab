"""Check 3 of MEASURED -> FORWARD: clears the floor declared beforehand —
the pair, EV per trade in net R and the minimum frequency. Never a floor
computed afterwards (R3, D5).

Since ADR-0050 (M16.21) the EV half is cleared by a **lower confidence
bound**: ``winner.ev - z(1 - alpha/k) * se``, where k is the declared sweep
and ``se`` is the winner's standard error clustered by entry date
(ADR-0048's). The winner is the best of k cells, so its point estimate is
biased upward and an effect sitting exactly at the floor passed about half
the time; simultaneous bounds at alpha/k cover every cell, so the winner's
holds after it is chosen. A question registered before the rule declared no
alternative to plan against and is judged as it was, by its point estimate,
with the bound recorded beside it; a re-score asks for the bound by name.
"""

from __future__ import annotations

from occams import inference
from occams.guards import Refusal

T = "MEASURED->FORWARD"
BOUND, POINT = "lower confidence bound", "point estimate (registered before ADR-0050)"


def evaluate(m, floor, plan=None, search_space_size: int = 1, *, bound: bool | None = None) -> tuple[Refusal | None, dict]:
    """The refusal, or None, and the numbers the check judged — the same on a pass (M16.8). ``bound`` forces the rule;
    left alone it is the bound for a question that declared an alternative and the point estimate for one that did not."""
    w = m.winner
    per_year = w.n / m.years if m.years > 0 else 0.0
    by_bound = bound if bound is not None else (plan is not None and getattr(plan, "alternative_ev_net_r", None) is not None)
    seen = {"ev_net_r": w.ev, "floor_ev_net_r": floor.ev_net_r, "n": w.n, "trades_per_year": per_year,
            "floor_min_trades_per_year": floor.min_trades_per_year, "years": m.years, "rule": BOUND if by_bound else POINT}
    se = dict(getattr(m, "winner_stats", ()) or ()).get("se_cluster")
    if plan is not None and se is not None:                    # the bound is recorded whichever rule judges
        alpha_c = plan.alpha / search_space_size
        seen.update({"alpha_corrected": alpha_c, "se_cluster": se, "lcb_ev_net_r": inference.lower_bound(w.ev, se, alpha_c)})
    if by_bound:
        if "lcb_ev_net_r" not in seen:
            r = Refusal(T, "floor: the measurement carries no standard error for the winner's EV, so no lower confidence bound "
                           "can be taken (ADR-0050)", {"ev_net_r": w.ev, "floor_ev_net_r": floor.ev_net_r, "n": w.n})
            return r, {**seen, "reason": r.reason}
        if seen["lcb_ev_net_r"] < floor.ev_net_r:
            r = Refusal(T, "floor: the lower confidence bound on EV is below the declared floor (ADR-0050)",
                        {"ev_net_r": w.ev, "lcb_ev_net_r": seen["lcb_ev_net_r"], "se_cluster": se, "alpha_corrected": seen["alpha_corrected"],
                         "floor_ev_net_r": floor.ev_net_r, "n": w.n})
            return r, {**seen, "reason": r.reason}
    elif w.ev < floor.ev_net_r:
        r = Refusal(T, "floor: EV per trade in net R is below the declared floor",
                    {"ev_net_r": w.ev, "floor_ev_net_r": floor.ev_net_r, "n": w.n})
        return r, {**seen, "reason": r.reason}
    if per_year < floor.min_trades_per_year:
        r = Refusal(T, "floor: trade frequency is below the declared minimum — the frequency half of the floor failed",
                    {"trades_per_year": per_year, "floor_min_trades_per_year": floor.min_trades_per_year,
                     "n": w.n, "years": m.years})
        return r, {**seen, "reason": r.reason}
    return None, seen


def check(m, floor, plan=None, search_space_size: int = 1, *, bound: bool | None = None) -> Refusal | None:
    return evaluate(m, floor, plan, search_space_size, bound=bound)[0]
