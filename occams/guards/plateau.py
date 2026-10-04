"""Check 1 of MEASURED -> FORWARD: a lone maximum is noise.

Ported from the donor's ``search.py:96-115`` — the Chebyshev-1 neighbourhood
of the winner must have at least ``plateau_cells`` members, the winner
counted, AND the winner's score must lie within ``plateau_slack`` of its
neighbours' median. The objective is the sweep's surface — the margin over
the passive alternative since ADR-0045, EV in net R before it — not P(pass)
(DESIGN §3).

Since ADR-0051 (M16.16): the median is the **neighbours'** — with the winner
in it, one of four cells is one of the two middle values and pulls the
median toward itself — and a question declares a second slack, in the
winner's own standard errors. Either slack exceeded is a refusal. A question
registered before the rule carries no slack in standard errors; for it the
gap in standard errors is recorded and not judged.
"""

from __future__ import annotations

from statistics import median

from occams.guards import Refusal

T = "MEASURED->FORWARD"


def neighbourhood(m, cell):
    """All cells within Chebyshev distance 1, the cell itself included."""
    return [c for c in m.cells if all(abs(a - b) <= 1 for a, b in zip(c.indices, cell.indices, strict=True))]


def _se_of_score(m) -> float | None:
    """The winner's standard error on the surface it won on: the margin's when the sweep is judged on the margin over
    its passive alternative (the fifth check's comparison), the EV's own otherwise. ADR-0048's, clustered by date."""
    stats = dict((m.baseline_stats if m.surface == "margin" else m.winner_stats) or ())
    se = stats.get("se_cluster")
    return float(se) if se is not None else None      # nil is a standard error: a winner that *is* its baseline has no error in its margin


def evaluate(m, gates) -> tuple[Refusal | None, dict]:
    """The refusal, or None, and the numbers the check judged — the same on a pass (M16.8)."""
    w = m.winner
    neigh = neighbourhood(m, w)
    size = {"neighbourhood": len(neigh), "plateau_cells": gates.plateau_cells, "winner": list(w.indices)}
    if len(neigh) < gates.plateau_cells:                      # the size is counted with the winner in it, as it was declared
        r = Refusal(T, "plateau: the winner's neighbourhood is too small to show a plateau", size)
        return r, {**size, "reason": r.reason}
    score = m.score(w)
    others = [m.score(c) for c in neigh if c.trades and c is not w]      # ADR-0051 §1: the winner is not in its own median
    med = median(others) if others else score                            # a single cell has no neighbours to be a spike above
    gap = score - med
    seen = {"winner_ev": w.ev, "winner_score": score, "surface": m.surface, "neighbourhood_median": med,
            "plateau_slack": gates.plateau_slack, "winner": list(w.indices)}
    se = _se_of_score(m)
    full = {**size, **seen, "gap": gap, "neighbours": len(others)}
    if se is not None:                                                    # recorded whether or not the question declared the slack
        full["se_score"] = se
        if se > 0:
            full["gap_se"] = gap / se
    slack_se = getattr(gates, "plateau_slack_se", None)
    if slack_se is not None:
        full["plateau_slack_se"] = slack_se
    if gap > gates.plateau_slack:
        r = Refusal(T, "plateau: lone spike — the winner exceeds its neighbourhood median by more than plateau_slack", seen)
        return r, {**full, "reason": r.reason}
    if slack_se is not None:                                             # ADR-0051 §2, §3: either slack exceeded is a refusal
        if se is None:
            r = Refusal(T, "plateau: the measurement carries no standard error for the winner's score, and the question declared a "
                           "slack in standard errors (ADR-0051)", {**seen, "plateau_slack_se": slack_se})
            return r, {**full, "reason": r.reason}
        if gap > slack_se * se:
            r = Refusal(T, "plateau: lone spike — the winner exceeds its neighbours' median by more than plateau_slack_se of its own "
                           "standard errors (ADR-0051)", {**seen, "plateau_slack_se": slack_se, "se_score": se,
                                                          **({"gap_se": gap / se} if se > 0 else {})})
            return r, {**full, "reason": r.reason}
    return None, full


def check(m, gates) -> Refusal | None:
    return evaluate(m, gates)[0]
