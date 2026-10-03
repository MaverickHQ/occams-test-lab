"""Check 3 of MEASURED -> FORWARD: clears the floor declared beforehand —
the pair, EV per trade in net R and the minimum frequency. Never a floor
computed afterwards (R3, D5)."""

from __future__ import annotations

from occams.guards import Refusal

T = "MEASURED->FORWARD"


def evaluate(m, floor) -> tuple[Refusal | None, dict]:
    """The refusal, or None, and the numbers the check judged — the same on a pass (M16.8)."""
    w = m.winner
    per_year = w.n / m.years if m.years > 0 else 0.0
    seen = {"ev_net_r": w.ev, "floor_ev_net_r": floor.ev_net_r, "n": w.n, "trades_per_year": per_year,
            "floor_min_trades_per_year": floor.min_trades_per_year, "years": m.years}
    if w.ev < floor.ev_net_r:
        r = Refusal(T, "floor: EV per trade in net R is below the declared floor",
                    {"ev_net_r": w.ev, "floor_ev_net_r": floor.ev_net_r, "n": w.n})
        return r, {**seen, "reason": r.reason}
    if per_year < floor.min_trades_per_year:
        r = Refusal(T, "floor: trade frequency is below the declared minimum — the frequency half of the floor failed",
                    {"trades_per_year": per_year, "floor_min_trades_per_year": floor.min_trades_per_year,
                     "n": w.n, "years": m.years})
        return r, {**seen, "reason": r.reason}
    return None, seen


def check(m, floor) -> Refusal | None:
    return evaluate(m, floor)[0]
