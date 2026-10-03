"""Strategy -> RETIRED. A retired Strategy returns only via a new
Hypothesis (D20). Retirement is recorded with its reason."""

from __future__ import annotations

from occams.guards import Refusal

T = "->RETIRED"


def check(s, ctx) -> Refusal | None:
    reason = getattr(ctx, "reason", "") or ""
    if not reason.strip():
        return Refusal(T, "retirement records its reason", {})
    return None
