"""Check 4 of MEASURED -> FORWARD: the pooled effect may not be carried by a
small minority of groups (ADR-0012). Leave each group out in turn; the
effect must survive every omission at ``loo_min_fraction`` of the pooled EV.

Fewer than three groups cannot show robustness, so that is a refusal, not a
pass — an engine measuring one instrument declares calendar blocks as its
groups."""

from __future__ import annotations

from occams.guards import Refusal

T = "MEASURED->FORWARD"
MIN_GROUPS = 3


def evaluate(m, gates) -> tuple[Refusal | None, dict]:
    """The refusal, or None, and the numbers the check judged — the same on a pass (M16.8)."""
    w = m.winner
    groups = w.groups
    if len(groups) < MIN_GROUPS:
        seen = {"groups": list(groups), "min_groups": MIN_GROUPS}
        r = Refusal(T, "leave-one-out: fewer than three groups, so robustness cannot be shown", seen)
        return r, {**seen, "reason": r.reason}
    pooled = m.score(w)                       # the surface: the margin over always-long since ADR-0045
    without = {g: m.score_without(w, g) for g in groups}
    weakest = min(groups, key=lambda g: without[g])
    seen = {"groups": len(groups), "pooled_ev": w.ev, "pooled_score": pooled, "surface": m.surface,
            "loo_min_fraction": gates.loo_min_fraction, "weakest_group": weakest, "weakest_score_without": without[weakest],
            "weakest_ev_without": w.ev_without(weakest)}
    for g in groups:
        if without[g] < gates.loo_min_fraction * pooled:
            r = Refusal(T, "leave-one-out: the pooled effect is carried by one group",
                        {"group": g, "ev_without": w.ev_without(g), "score_without": without[g], "pooled_ev": w.ev,
                         "pooled_score": pooled, "surface": m.surface,
                         "loo_min_fraction": gates.loo_min_fraction, "groups": len(groups)})
            return r, {**seen, **r.evidence, "reason": r.reason}
    return None, seen


def check(m, gates) -> Refusal | None:
    return evaluate(m, gates)[0]
