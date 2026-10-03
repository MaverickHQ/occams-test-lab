"""M16.7 (ADR-0047 §6; the review's F23) — the size-and-power table as tests: each Monte
Carlo guard in isolation, over hundreds of seeds, on a world whose truth is known, against
the rate the guard declares. Marked ``calibration``: minutes, not milliseconds, so they run
from ``make calibrate`` and a scheduled workflow and never from ``make check``.

A row the review found outside tolerance is a **strict expected failure naming the row of
the task list that fixes it**: `main` stays green, and the day the guard is fixed the test
passes, the strict mark fails the run, and the fix removes the mark. The seeds are fixed, so
a rate here is a number, not a draw.
"""

from __future__ import annotations

import pytest

from occams import calibrate
from occams.calibrate import ALPHAS, ROWS, row, within

pytestmark = pytest.mark.calibration


def _within(world: str, guard: str) -> None:
    r = row(world, guard)
    for alpha in ALPHAS:
        ok, got, bound = within(r, alpha)
        assert ok, f"{r.engine} {guard} on {r.world}: {got:.3f} at alpha {alpha}, tolerance {bound:.3f} over {r.seeds} seeds"


def test_day_boxed_null_holds_size_without_dependence():
    """The control of the controls: independent names, one box a day — the as-built null is right here."""
    _within("day_boxed:martingale-rho0.0", "beats_null")


@pytest.mark.xfail(strict=True, reason="M16.14 (ADR-0048): the null is resampled as if every trade were independent of the others on its date")
def test_day_boxed_null_holds_size_under_common_factor():
    """The review's F02: names that share a market make same-date trades move together."""
    _within("day_boxed:martingale-rho0.5", "beats_null")


@pytest.mark.xfail(strict=True, reason="M16.14 (ADR-0048): the null is resampled at the random-entry pool's count, not the winner's")
def test_position_boxed_null_holds_size_on_empty_world():
    """The review's F01: a world with nothing in it, and a guard that passes it fourteen times in a hundred."""
    _within("position_boxed:martingale-rho0.0", "beats_null")


@pytest.mark.xfail(strict=True, reason="M16.14 (ADR-0048): both defects at once — the pool's count, and trades that share a date")
def test_position_boxed_null_holds_size_under_common_factor():
    _within("position_boxed:martingale-rho0.5", "beats_null")


def test_fifth_check_holds_size_for_a_long_entry_with_no_timing_skill():
    """The fifth check's own control: on a rising market a long entry with no timing skill is refused as built."""
    _within("day_boxed:updrift-rho0.5", "beats_always_long")


@pytest.mark.xfail(strict=True, reason="M16.15 (ADR-0049): always-long is resampled at its own count, not the winner's, on the multi-day engine")
def test_fifth_check_holds_size_on_empty_world_position_boxed():
    _within("position_boxed:martingale-rho0.0", "beats_always_long")


@pytest.mark.xfail(strict=True, reason="M16.15 (ADR-0049): the baseline is long on every box whatever the winner's side — "
                                       "a coin flip beats it by being short half the time")
def test_fifth_check_refuses_coin_flip_on_drifting_paths():
    """The review's F04: on a market that falls, a coin flip passes the check that is meant to attest the entry."""
    _within("day_boxed:downdrift-rho0.0:coin", "beats_always_long")


def test_every_row_of_the_table_is_a_test_here():
    """A row added to the table without a test would be printed and never enforced."""
    import inspect

    source = inspect.getsource(inspect.getmodule(test_every_row_of_the_table_is_a_test_here))
    for r in ROWS:
        assert f'_within("{r.key}", "{r.guard}")' in source, (r.key, r.guard)
        assert r.kind in ("size", "power") and r.seeds >= (calibrate.SIZE_SEEDS if r.kind == "size" else calibrate.POWER_SEEDS)
