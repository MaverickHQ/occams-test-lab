"""Strategy SPECIFIED -> COMPILED. Every Strategy declares a stop (D5); a
spec without one fails to compile. The full geometry check arrives with the
StrategySpec at M3.4; the stop's existence is checkable now."""

from __future__ import annotations

from occams.guards import Refusal

T = "SPECIFIED->COMPILED"


def check(s, ctx) -> Refusal | None:
    if getattr(s, "spec", None) is not None:
        from occams.spec.compile import CompileError, validate

        try:
            validate(s.spec)
        except CompileError as e:
            return Refusal(T, f"does not compile: {e}", {"spec_hash": s.spec_hash})
        return None
    identity = dict(s.identity)
    stop = identity.get("stop")
    if stop is None:
        return Refusal(T, "no stop declared — every Strategy declares a stop (D5)", {"identity_keys": sorted(identity)})
    try:
        if float(stop) <= 0:
            return Refusal(T, "stop must be positive", {"stop": stop})
    except (TypeError, ValueError):
        return Refusal(T, "stop is not a number", {"stop": stop})
    return None
