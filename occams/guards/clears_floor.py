"""Check 3 of MEASURED -> FORWARD: clears the floor declared beforehand —
the pair, EV per trade in net R and the minimum frequency. Never a floor
computed afterwards (R3, D5)."""

from __future__ import annotations

from occams.guards import Refusal

T = "MEASURED->FORWARD"


def check(m, floor) -> Refusal | None:
    w = m.winner
    if w.ev < floor.ev_net_r:
        return Refusal(T, "floor: EV per trade in net R is below the declared floor",
                       {"ev_net_r": w.ev, "floor_ev_net_r": floor.ev_net_r, "n": w.n})
    per_year = w.n / m.years if m.years > 0 else 0.0
    if per_year < floor.min_trades_per_year:
        return Refusal(T, "floor: trade frequency is below the declared minimum — the frequency half of the floor failed",
                       {"trades_per_year": per_year, "floor_min_trades_per_year": floor.min_trades_per_year,
                        "n": w.n, "years": m.years})
    return None
