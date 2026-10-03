"""Check 2 of MEASURED -> FORWARD: beats random entry under the same costs
and geometry, Monte Carlo, at the Bonferroni-corrected alpha (R4.4).

A null with too few draws to resolve the corrected alpha cannot say no, so
it is refused rather than passed — the vacuous pass is the defect this lab
exists to refuse.

Since ADR-0048 (M16.14): the draws are means at the winner's own count, or
the check refuses; and a standard error clustered by date is read beside
the bootstrap — when the two fall on opposite sides of the corrected alpha
the check refuses, naming both.
"""

from __future__ import annotations

from occams import inference
from occams.guards import Refusal

T = "MEASURED->FORWARD"
DRAWS_PER_ALPHA = inference.DRAWS_PER_ALPHA  # at least this many expected exceedances, or the distribution cannot say no


def evaluate(m, plan, search_space_size: int) -> tuple[Refusal | None, dict]:
    """The refusal, or None, and the numbers the check judged — the same on a pass (M16.8)."""
    w = m.winner
    alpha_c = plan.alpha / search_space_size
    dist = m.null_ev
    state, p, need = inference.exceedance(dist, w.ev, alpha_c)      # counted plus one (ADR-0048 §4): never zero
    if state == "thin":
        seen = {"draws": len(dist), "needed": need, "alpha_corrected": alpha_c}
        r = Refusal(T, "beats-null: the null distribution is too thin to say no at the corrected alpha", seen)
        return r, {**seen, "reason": r.reason}
    if m.null_n != w.n:                                              # ADR-0048 §1: every draw is a mean at the winner's count
        seen = {"null_n": m.null_n, "n": w.n, "draws": len(dist), "alpha_corrected": alpha_c}
        r = Refusal(T, "beats-null: the null was not drawn at the winner's count (ADR-0048)", seen)
        return r, {**seen, "reason": r.reason}
    seen = {"p_null": p, "alpha_corrected": alpha_c, "winner_ev": w.ev, "null_mean": sum(dist) / len(dist), "draws": len(dist)}
    full = {**seen, "needed": need, **inference.beside(m.null_stats, w)}
    if state == "refuse":
        r = Refusal(T, "beats-null: random entry under the same geometry does as well", seen)
        return r, {**full, "reason": r.reason}
    if full.get("p_cluster") is None:
        r = Refusal(T, "beats-null: the measurement carries no clustered standard error to check the bootstrap against (ADR-0048)", seen)
        return r, {**full, "reason": r.reason}
    if full["p_cluster"] > alpha_c:                                  # ADR-0048 §5: two answers to one question
        r = Refusal(T, "beats-null: the bootstrap and the clustered standard error disagree at the corrected alpha (ADR-0048)",
                    {**seen, "p_cluster": full["p_cluster"], "se_cluster": full["se_cluster"]})
        return r, {**full, "reason": r.reason}
    return None, full


def check(m, plan, search_space_size: int) -> Refusal | None:
    return evaluate(m, plan, search_space_size)[0]
