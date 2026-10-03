"""Strategy HALTED -> LIVE. Resuming needs the halting condition cleared on
its own terms AND a recorded human action (D20, ADR-0024). Neither can be
satisfied before M10.15 builds the causes, so this refuses until then."""

from __future__ import annotations

from occams.guards import Refusal

T = "HALTED->LIVE"


def check(s, ctx) -> Refusal | None:
    if not getattr(ctx, "cause_cleared", False):
        return Refusal(T, "the halting cause has not cleared on its own terms", {})
    if not (getattr(ctx, "resumed_by", "") or "").strip():
        return Refusal(T, "resuming requires a recorded human action", {})
    return Refusal(T, "halt causes are not built yet (M10.15); nothing resumes before they are", {})
