"""Check 2 of MEASURED -> FORWARD: beats random entry under the same costs
and geometry, Monte Carlo, at the Bonferroni-corrected alpha (R4.4).

A null with too few draws to resolve the corrected alpha cannot say no, so
it is refused rather than passed — the vacuous pass is the defect this lab
exists to refuse.
"""

from __future__ import annotations

import math

from occams.guards import Refusal

T = "MEASURED->FORWARD"
DRAWS_PER_ALPHA = 20  # at least this many expected exceedances under the null


def check(m, plan, search_space_size: int) -> Refusal | None:
    w = m.winner
    alpha_c = plan.alpha / search_space_size
    need = math.ceil(DRAWS_PER_ALPHA / alpha_c)
    if len(m.null_ev) < need:
        return Refusal(T, "beats-null: the null distribution is too thin to say no at the corrected alpha",
                       {"draws": len(m.null_ev), "needed": need, "alpha_corrected": alpha_c})
    exceed = sum(1 for x in m.null_ev if x >= w.ev)
    p = exceed / len(m.null_ev)
    if p > alpha_c:
        return Refusal(T, "beats-null: random entry under the same geometry does as well",
                       {"p_null": p, "alpha_corrected": alpha_c, "winner_ev": w.ev,
                        "null_mean": sum(m.null_ev) / len(m.null_ev), "draws": len(m.null_ev)})
    return None
