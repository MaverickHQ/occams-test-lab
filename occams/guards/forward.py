"""Strategy MEASURED -> FORWARD: GOOD SETUP? is five refusals (DESIGN §3, ADR-0043),
all evaluated, all recorded — the Register says which fired, not only that
one did, and since M16.8 what each one saw, passing or failing."""

from __future__ import annotations

from occams.guards import Refusal, beats_always_long, beats_null, clears_floor, leave_one_out, plateau

CHECKS = ("plateau", "beats_null", "clears_floor", "leave_one_out", "beats_always_long")


def check(m, h) -> tuple[Refusal, ...] | None:
    fired = tuple(r for r, _ in evaluations(m, h) if r is not None)
    return fired or None


def passes(m, h) -> tuple[str, ...]:
    """The names of the checks that pass, for a record that says so."""
    return tuple(name for name, (r, _) in zip(CHECKS, evaluations(m, h), strict=True) if r is None)


def evidence(m, h) -> tuple[tuple[str, bool, dict], ...]:
    """(check, passed, the numbers it judged) for each of the five, in order — what a
    resolution records before it resolves, pass or fail (M16.8)."""
    return tuple((name, r is None, dict(seen)) for name, (r, seen) in zip(CHECKS, evaluations(m, h), strict=True))


def evaluations(m, h) -> tuple[tuple[Refusal | None, dict], ...]:
    """Each check evaluated once: its refusal or None, and what it saw."""
    return (plateau.evaluate(m, h.gates),
            beats_null.evaluate(m, h.power_plan, h.search_space_size),
            clears_floor.evaluate(m, h.floor),
            leave_one_out.evaluate(m, h.gates),
            beats_always_long.evaluate(m, h.power_plan, h.search_space_size))
