"""Strategy FORWARD -> APPROVED. May not enter APPROVED without citing a
resolved Hypothesis whose verdict supports it, and the deployed hash must
equal the resolved hash (F0, ADR-0002)."""

from __future__ import annotations

from occams.guards import Refusal

T = "FORWARD->APPROVED"


def check(s, ctx) -> Refusal | None:
    from occams.hypothesis import HypothesisState

    h = getattr(ctx, "hypothesis", None)
    if h is None:
        return Refusal(T, "approval cites no Hypothesis", {})
    if h.state is not HypothesisState.RESOLVED or h.verdict is None:
        return Refusal(T, "the cited Hypothesis is not resolved", {"state": h.state.value})
    if h.verdict.outcome != "supported":
        return Refusal(T, "the cited Hypothesis resolved null; only the Strategy that rested on it is retired",
                       {"outcome": h.verdict.outcome})
    if h.verdict.spec_hash != s.spec_hash:
        return Refusal(T, "deployed hash must equal resolved hash (D2)", {"resolved": h.verdict.spec_hash, "deploying": s.spec_hash})
    if h.verdict.cost_basis not in ("bounded", "measured"):
        return Refusal(T, "approval needs a verdict reached under the conservative cost bound or measured costs (D23); "
                          "a Strategy clearing its floor only under optimistic costs is refused",
                       {"cost_basis": h.verdict.cost_basis})
    return None
