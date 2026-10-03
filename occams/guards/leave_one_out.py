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


def check(m, gates) -> Refusal | None:
    w = m.winner
    groups = w.groups
    if len(groups) < MIN_GROUPS:
        return Refusal(T, "leave-one-out: fewer than three groups, so robustness cannot be shown",
                       {"groups": list(groups), "min_groups": MIN_GROUPS})
    pooled = m.score(w)                       # the surface: the margin over always-long since ADR-0045
    for g in groups:
        without = m.score_without(w, g)
        if without < gates.loo_min_fraction * pooled:
            return Refusal(T, "leave-one-out: the pooled effect is carried by one group",
                           {"group": g, "ev_without": w.ev_without(g), "score_without": without, "pooled_ev": w.ev,
                            "pooled_score": pooled, "surface": m.surface,
                            "loo_min_fraction": gates.loo_min_fraction, "groups": len(groups)})
    return None
