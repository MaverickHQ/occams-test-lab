"""Strategy MEASURED -> FORWARD: GOOD SETUP? is five refusals (DESIGN §3, ADR-0043),
all evaluated, all recorded — the Register says which fired, not only that
one did."""

from __future__ import annotations

from occams.guards import Refusal, beats_always_long, beats_null, clears_floor, leave_one_out, plateau

CHECKS = ("plateau", "beats_null", "clears_floor", "leave_one_out", "beats_always_long")


def check(m, h) -> tuple[Refusal, ...] | None:
    results = _results(m, h)
    fired = tuple(r for r in results if r is not None)
    return fired or None


def passes(m, h) -> tuple[str, ...]:
    """The names of the checks that pass, for a record that says so."""
    return tuple(name for name, r in zip(CHECKS, _results(m, h)) if r is None)


def _results(m, h):
    return (plateau.check(m, h.gates),
            beats_null.check(m, h.power_plan, h.search_space_size),
            clears_floor.check(m, h.floor),
            leave_one_out.check(m, h.gates),
            beats_always_long.check(m, h.power_plan, h.search_space_size))
