"""Hypothesis DRAFT -> REGISTERED. The act that spends alpha (R4.8)."""

from __future__ import annotations

from occams.guards import Refusal

T = "DRAFT->REGISTERED"


def check(h, *, confirmation, parent, budget=None, declared=None) -> Refusal | None:
    from occams.hypothesis import HypothesisState, Tier

    if h.state is not HypothesisState.DRAFT:
        return Refusal(T, "not a draft", {"state": h.state.value})
    missing = [k for k in ("mechanism", "if_true", "if_false", "falsifier") if not getattr(h, k, "").strip()]
    if missing:
        return Refusal(T, "draft is incomplete — a Hypothesis states its mechanism, both interpretations and its falsifier before it costs anything",
                       {"missing": missing})
    if h.floor.ev_net_r <= 0 or h.floor.min_trades_per_year <= 0:
        return Refusal(T, "declared floor must be a positive pair", {"floor": [h.floor.ev_net_r, h.floor.min_trades_per_year]})
    slack_se = getattr(h.gates, "plateau_slack_se", None)
    if slack_se is None:
        return Refusal(T, "a registration declares plateau_slack_se — the slack, in the winner's own standard errors, beyond which "
                          "the plateau check refuses (ADR-0051); it has no default", {"gates": "plateau_slack_se"})
    if not slack_se > 0:
        return Refusal(T, "plateau_slack_se must be positive", {"plateau_slack_se": slack_se})
    if h.search_space_size < 1:
        return Refusal(T, "search_space_size must be at least 1", {"search_space_size": h.search_space_size})
    p = h.power_plan
    if p.sigma_r <= 0 or not (0 < p.alpha < 1) or not (0 < p.power < 1) or p.available_n < 0:
        return Refusal(T, "power plan is not well-formed", {"sigma_r": p.sigma_r, "alpha": p.alpha, "power": p.power, "available_n": p.available_n})
    alternative = getattr(p, "alternative_ev_net_r", None)
    if alternative is None:
        return Refusal(T, "a registration declares alternative_ev_net_r — the EV the question wants power at, beside its floor "
                          "(ADR-0050); it has no default", {"power": "alternative_ev_net_r"})
    if not alternative > h.floor.ev_net_r:
        return Refusal(T, "the declared alternative must be strictly above the floor (ADR-0050)",
                       {"alternative_ev_net_r": alternative, "floor_ev_net_r": h.floor.ev_net_r})
    if not confirmation.by.strip():
        return Refusal(T, "registration needs a named confirmation", {})
    if not h.capability:
        if budget is None:
            return Refusal(T, "a market question registers through the accountant; only a capability question registers at alpha 0 (R4.6)", {})
        if not confirmation.human:
            return Refusal(T, "spending alpha requires a human confirmation (R4.8); only a capability question at alpha 0 may confirm itself",
                           {"by": confirmation.by})
    if h.tier is Tier.IMPLEMENTATION:
        if parent is None or h.parent_id is None or parent.id != h.parent_id:
            return Refusal(T, "an implementation Hypothesis cannot exist without a resolved mechanism parent (ADR-0027)",
                           {"parent_id": h.parent_id})
        if parent.tier is not Tier.MECHANISM:
            return Refusal(T, "parent must be a mechanism Hypothesis", {"parent_tier": parent.tier.value})
        if parent.state is not HypothesisState.RESOLVED:
            return Refusal(T, "parent mechanism is not resolved", {"parent_state": parent.state.value})
        if parent.axis is not h.axis:
            return Refusal(T, "parent mechanism is on a different axis; implementation spends from its parent's axis",
                           {"parent_axis": parent.axis.value, "axis": h.axis.value})
        if parent.verdict is None or parent.verdict.outcome != "supported":
            return Refusal(T, "parent mechanism resolved null; nothing to implement", {"parent_outcome": getattr(parent.verdict, "outcome", None)})
    elif h.parent_id is not None:
        return Refusal(T, "a mechanism Hypothesis has no parent", {"parent_id": h.parent_id})
    if not h.capability:
        # M6.5: the parent check above ran BEFORE any spend; now the budget, then the overlap gate
        r = budget.check(h.axis, h.tier, h.search_space_size)
        if r is not None:
            return r
        if declared is not None:
            from occams.ledger.alpha_budget import SearchBudget

            r = SearchBudget(budget.register).gate(declared, threshold=budget.cfg.lab.overlap_threshold,
                                                   supersedes=h.supersedes, distinction=h.distinction)
            if r is not None:
                return r
    return None
