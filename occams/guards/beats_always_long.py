"""Check 5 of MEASURED -> FORWARD (ADR-0043): beats always-long at the same
geometry and gate, Monte Carlo, at the Bonferroni-corrected alpha (R4.4).

Beats-null asks *better than chance?* against a two-sided null. This asks
*better than the passive alternative?* — long on every box under the same
exits, stop, horizon and regime gate, with no entry signal at all — so a
supported verdict attests the entry, not the gate and the side. An engine
supplies the distribution in ``Measurement.baseline_ev``; one too thin to
resolve the corrected alpha, or absent, is refused, never passed.
"""

from __future__ import annotations

import math

from occams.guards import Refusal

T = "MEASURED->FORWARD"
DRAWS_PER_ALPHA = 20  # at least this many expected exceedances under always-long


def check(m, plan, search_space_size: int) -> Refusal | None:
    w = m.winner
    alpha_c = plan.alpha / search_space_size
    need = math.ceil(DRAWS_PER_ALPHA / alpha_c)
    base = tuple(getattr(m, "baseline_ev", ()) or ())
    if len(base) < need:
        return Refusal(T, "beats-always-long: the always-long distribution is too thin to say no at the corrected alpha",
                       {"draws": len(base), "needed": need, "alpha_corrected": alpha_c})
    exceed = sum(1 for x in base if x >= w.ev)
    p = exceed / len(base)
    if p > alpha_c:
        return Refusal(T, "beats-always-long: being long at the same geometry and gate does as well",
                       {"p_baseline": p, "alpha_corrected": alpha_c, "winner_ev": w.ev,
                        "baseline_mean": sum(base) / len(base), "draws": len(base)})
    return None
