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

from occams import inference
from occams.guards import Refusal

T = "MEASURED->FORWARD"
DRAWS_PER_ALPHA = inference.DRAWS_PER_ALPHA  # at least this many expected exceedances, or the distribution cannot say no


def evaluate(m, plan, search_space_size: int) -> tuple[Refusal | None, dict]:
    """The refusal, or None, and the numbers the check judged — the same on a pass (M16.8)."""
    w = m.winner
    alpha_c = plan.alpha / search_space_size
    dist = tuple(getattr(m, "baseline_ev", ()) or ())
    state, p, need = inference.exceedance(dist, w.ev, alpha_c)      # counted plus one (ADR-0048 §4): never zero
    if state == "thin":
        seen = {"draws": len(dist), "needed": need, "alpha_corrected": alpha_c}
        r = Refusal(T, "beats-always-long: the always-long distribution is too thin to say no at the corrected alpha", seen)
        return r, {**seen, "reason": r.reason}
    seen = {"p_baseline": p, "alpha_corrected": alpha_c, "winner_ev": w.ev, "baseline_mean": sum(dist) / len(dist), "draws": len(dist)}
    if state == "refuse":
        r = Refusal(T, "beats-always-long: being long at the same geometry and gate does as well", seen)
        return r, {**seen, "needed": need, "reason": r.reason}
    return None, {**seen, "needed": need}


def check(m, plan, search_space_size: int) -> Refusal | None:
    return evaluate(m, plan, search_space_size)[0]
