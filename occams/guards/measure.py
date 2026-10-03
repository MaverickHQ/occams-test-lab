"""Hypothesis REGISTERED -> MEASURED. If underpowered: say so and do not run
it (M8.2, DESIGN §10). A sample problem found now is a refusal now."""

from __future__ import annotations

from occams.guards import Refusal

T = "REGISTERED->MEASURED"


def check(h, m) -> Refusal | None:
    from occams.hypothesis import HypothesisState

    if h.state is not HypothesisState.REGISTERED:
        return Refusal(T, "not registered", {"state": h.state.value})
    need = h.required_n
    if h.power_plan.available_n < need:
        return Refusal(T, "underpowered: the measurement partition cannot see the declared floor",
                       {"required_n": need, "available_n": h.power_plan.available_n,
                        "floor_ev_net_r": h.floor.ev_net_r, "sigma_r": h.power_plan.sigma_r,
                        "alpha_corrected": h.power_plan.alpha / h.search_space_size})
    if m.search_space_size != h.search_space_size:
        return Refusal(T, "the sweep that ran is not the sweep that was declared (R4.4)",
                       {"declared": h.search_space_size, "ran": m.search_space_size})
    if m.winner.n < need:
        return Refusal(T, "the winning cell holds fewer trades than the power plan requires",
                       {"required_n": need, "n": m.winner.n})
    if not m.spec_hash:
        return Refusal(T, "measurement carries no spec hash", {})
    return None
