"""Check 1 of MEASURED -> FORWARD: a lone maximum is noise.

Ported from the donor's ``search.py:96-115`` — the Chebyshev-1 neighbourhood
of the winner (including the winner) must have at least ``plateau_cells``
members AND a median within ``plateau_slack`` of the winner. The objective
is the sweep's surface — the margin over always-long since ADR-0045, EV
in net R before it — not P(pass) (DESIGN §3).
"""

from __future__ import annotations

from statistics import median

from occams.guards import Refusal

T = "MEASURED->FORWARD"


def neighbourhood(m, cell):
    """All cells within Chebyshev distance 1, the cell itself included."""
    return [c for c in m.cells if all(abs(a - b) <= 1 for a, b in zip(c.indices, cell.indices))]


def check(m, gates) -> Refusal | None:
    w = m.winner
    neigh = neighbourhood(m, w)
    if len(neigh) < gates.plateau_cells:
        return Refusal(T, "plateau: the winner's neighbourhood is too small to show a plateau",
                       {"neighbourhood": len(neigh), "plateau_cells": gates.plateau_cells, "winner": list(w.indices)})
    score = m.score(w)
    med = median(m.score(c) for c in neigh if c.trades)
    if score - med > gates.plateau_slack:
        return Refusal(T, "plateau: lone spike — the winner exceeds its neighbourhood median by more than plateau_slack",
                       {"winner_ev": w.ev, "winner_score": score, "surface": m.surface, "neighbourhood_median": med,
                        "plateau_slack": gates.plateau_slack, "winner": list(w.indices)})
    return None
