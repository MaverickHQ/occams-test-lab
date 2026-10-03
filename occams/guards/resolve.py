"""Hypothesis MEASURED -> RESOLVED. The Verdict freezes the spec hash (D2)."""

from __future__ import annotations

from occams.guards import Refusal

T = "MEASURED->RESOLVED"


def check(h, v) -> Refusal | None:
    from occams.hypothesis import HypothesisState

    if h.state is not HypothesisState.MEASURED:
        return Refusal(T, "not measured", {"state": h.state.value})
    family = getattr(v, "family_hash", "") or ""
    if family:
        # ADR-0036: the verdict freezes the winner cell's hash; the family it names must be the template measured
        if family != h.spec_hash:
            return Refusal(T, "verdict names a different family than the template measured (D2, ADR-0036)",
                           {"measured": h.spec_hash, "family": family, "winner": v.spec_hash})
    elif v.spec_hash != h.spec_hash:
        return Refusal(T, "verdict names a different spec than the one measured (D2)",
                       {"measured": h.spec_hash, "verdict": v.spec_hash})
    if v.outcome not in ("supported", "null"):
        return Refusal(T, "outcome must be supported or null", {"outcome": v.outcome})
    clears = v.ev_net_r >= h.floor.ev_net_r and v.trades_per_year >= h.floor.min_trades_per_year and not v.refusals
    if (v.outcome == "supported") != clears:
        return Refusal(T, "outcome contradicts the floor declared beforehand",
                       {"outcome": v.outcome, "ev_net_r": v.ev_net_r, "trades_per_year": v.trades_per_year,
                        "floor": [h.floor.ev_net_r, h.floor.min_trades_per_year], "refusals": list(v.refusals)})
    return None
