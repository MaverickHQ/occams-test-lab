"""The reserve permits one look per spec hash, ever (F18.4, ADR-0006, M4.7).
The look is recorded against the hash in the Register; a second is refused.
Another look needs a different spec — a new hash, a new Hypothesis, new
alpha."""

from __future__ import annotations

from occams.guards import Refusal, refuse_or_pass

T = "RESERVE-LOOK"


def check(spec_hash: str, register) -> Refusal | None:
    prior = [r for r in register.records() if r["type"] == "ReserveLook" and r["spec_hash"] == spec_hash]
    if prior:
        return Refusal(T, "the reserve has already been looked at for this spec hash; a second look is refused",
                       {"spec_hash": spec_hash, "first_look_by": prior[0]["hypothesis_id"], "at": prior[0]["at"]})
    return None


def look(spec_hash: str, hypothesis_id: str, register) -> None:
    refuse_or_pass(check(spec_hash, register), register, spec_hash=spec_hash, hypothesis_id=hypothesis_id)
    register.append(register.ReserveLook(spec_hash, hypothesis_id))
