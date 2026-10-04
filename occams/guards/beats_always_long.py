"""Check 5 of MEASURED -> FORWARD (ADR-0043): beats the passive alternative at the
same geometry and gate, Monte Carlo, at the Bonferroni-corrected alpha (R4.4).

Beats-null asks *better than chance?* against a coin's side. This asks
*better than doing nothing clever?* — a market entry on every box the gate
admits, under the same exits, stop and horizon, with no entry signal at all —
so a supported verdict attests the entry, not the gate and the side.

Since ADR-0049 (M16.15) the passive alternative takes the winner's own side
mix: always-long for a long-only entry, as before, and the coin's own
expectation for a coin, which was passing this check on a falling market by
being short half the time. Winner and baseline are resampled together by
calendar day at the winner's count (ADR-0048), and a standard error clustered
by date is read beside the bootstrap. A distribution too thin to resolve the
corrected alpha, absent, or drawn at another count is refused, never passed.
"""

from __future__ import annotations

from occams import inference
from occams.guards import Refusal

T = "MEASURED->FORWARD"
DRAWS_PER_ALPHA = inference.DRAWS_PER_ALPHA  # at least this many expected exceedances, or the distribution cannot say no


REFUSED = "beats-always-long: the passive alternative at the same geometry, gate and side mix does as well"


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
    if m.baseline_n != w.n:                                          # ADR-0048 §1: every draw is a mean at the winner's count
        seen = {"baseline_n": m.baseline_n, "n": w.n, "draws": len(dist), "alpha_corrected": alpha_c}
        r = Refusal(T, "beats-always-long: the baseline was not drawn at the winner's count (ADR-0048)", seen)
        return r, {**seen, "reason": r.reason}
    stats = dict(m.baseline_stats or ())
    seen = {"p_baseline": p, "alpha_corrected": alpha_c, "winner_ev": w.ev, "baseline_mean": sum(dist) / len(dist), "draws": len(dist)}
    full = {**seen, "needed": need, **inference.beside(m.baseline_stats, w),
            **{k: stats[k] for k in ("long_share", "selection", "execution") if k in stats}}
    if state == "refuse":
        r = Refusal(T, REFUSED, seen)
        return r, {**full, "reason": r.reason}
    if full.get("p_cluster") is None:
        r = Refusal(T, "beats-always-long: the measurement carries no clustered standard error to check the bootstrap against (ADR-0048)",
                    seen)
        return r, {**full, "reason": r.reason}
    if full["p_cluster"] > alpha_c:                                  # ADR-0048 §5: two answers to one question
        r = Refusal(T, "beats-always-long: the bootstrap and the clustered standard error disagree at the corrected alpha (ADR-0048)",
                    {**seen, "p_cluster": full["p_cluster"], "se_cluster": full["se_cluster"]})
        return r, {**full, "reason": r.reason}
    return None, full


def check(m, plan, search_space_size: int) -> Refusal | None:
    return evaluate(m, plan, search_space_size)[0]
