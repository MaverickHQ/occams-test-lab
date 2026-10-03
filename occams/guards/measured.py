"""Strategy COMPILED -> MEASURED. The measurement must be of this spec, by a
named engine, with its partition stamped."""

from __future__ import annotations

from occams.guards import Refusal

T = "COMPILED->MEASURED"


def check(s, ctx) -> Refusal | None:
    m = getattr(ctx, "measurement", None)
    if m is None:
        return Refusal(T, "no measurement supplied", {})
    cells = {getattr(c, "spec_hash", None) for c in getattr(m, "cells", ())}
    if m.spec_hash != s.spec_hash and s.spec_hash not in cells:
        # ADR-0036: the family's Measurement measures every cell; the winner's Strategy is one of them
        return Refusal(T, "measurement is of a different spec (D2)", {"strategy": s.spec_hash, "measurement": m.spec_hash})
    if not m.engine or not m.engine_sha:
        return Refusal(T, "measurement names no engine or engine_sha", {"engine": m.engine, "engine_sha": m.engine_sha})
    if not m.partition or m.years <= 0:
        return Refusal(T, "measurement carries no partition", {"partition": m.partition, "years": m.years})
    if not m.cells:
        return Refusal(T, "measurement has no cells", {})
    return None
