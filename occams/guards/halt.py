"""Strategy LIVE -> HALTED. Any human may halt anything without
justification (D20). A halt is attributable, not justified — the one thing
it needs is a name."""

from __future__ import annotations

from occams.guards import Refusal

T = "LIVE->HALTED"


def check(s, ctx) -> Refusal | None:
    by = getattr(ctx, "halted_by", "") or ""
    if not by.strip():
        return Refusal(T, "a halt is attributable: name who halted", {})
    return None
