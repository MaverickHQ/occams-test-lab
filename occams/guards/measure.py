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
    stats = dict(getattr(m, "winner_stats", ()) or ())
    if stats.get("sd") is not None and stats.get("n_eff") is not None:
        # ADR-0050 §4: the plan promised power at one dispersion and any cell of the sweep may win. Recomputed on the
        # formula the question registered with, at the winner's own. It reads the measurement partition and can only refuse.
        from dataclasses import replace

        need_w = replace(h.power_plan, sigma_r=max(float(stats["sd"]), 1e-12)).required_n(h.floor, h.search_space_size)
        if float(stats["n_eff"]) < need_w:
            return Refusal(T, "underpowered at the winning cell's own dispersion (ADR-0050)",
                           {"winner_sd": stats["sd"], "plan_sigma_r": h.power_plan.sigma_r, "required_n": need,
                            "required_n_at_winner_sd": need_w, "n": m.winner.n, "n_eff": stats["n_eff"],
                            "se_cluster": stats.get("se_cluster")})
    if not m.spec_hash:
        return Refusal(T, "measurement carries no spec hash", {})
    return None
