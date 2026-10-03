"""Strategy APPROVED -> LIVE. Human-only, by signature (R1.1, D18). The
signature type arrives at M10.6; until it exists this guard refuses
everything, which is the only safe state for an unbuilt gate."""

from __future__ import annotations

from occams.guards import Refusal

T = "APPROVED->LIVE"


def check(s, ctx) -> Refusal | None:
    sig = getattr(ctx, "signature", None)
    if sig is None:
        return Refusal(T, "APPROVED->LIVE requires a human signature over the spec hash; none supplied", {})
    return Refusal(T, "signatures are not built yet (M10.6); no agent, scheduler or automated path performs this transition",
                   {"supplied": type(sig).__name__})
