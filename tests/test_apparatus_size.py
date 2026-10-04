"""M16.7 (ADR-0047 §6; the review's F23) — the size-and-power table as tests: each Monte
Carlo guard in isolation, over hundreds of seeds, on a world whose truth is known, against
the rate the guard declares. Marked ``calibration``: minutes, not milliseconds, so they run
from ``make calibrate`` and a scheduled workflow and never from ``make check``.

A row outside tolerance is a **strict expected failure naming the row of the task list that
fixes it** — or, for the one residual no row closes, the ADR that records it: `main` stays
green, and the day the guard is fixed the test passes, the strict mark fails the run, and the
fix removes the mark. The seeds are fixed, so a rate here is a number, not a draw.
"""

from __future__ import annotations

import pytest

from occams import calibrate
from occams.calibrate import ROWS, row, within

pytestmark = pytest.mark.calibration


def _within(world: str, guard: str, alphas=None) -> None:
    r = row(world, guard)
    for alpha in alphas or r.alphas:
        ok, got, bound = within(r, alpha)
        assert ok, f"{r.engine} {guard} on {r.world}: {got:.3f} at alpha {alpha}, tolerance {bound:.3f} over {r.seeds} seeds"


def test_day_boxed_null_holds_size_without_dependence():
    """The control of the controls: independent names, one box a day."""
    _within("day_boxed:martingale-rho0.0", "beats_null")


def test_day_boxed_null_holds_size_under_common_factor():
    """The review's F02: names that share a market make same-date trades move together. 0.095 and 0.200 as built;
    within tolerance since M16.14 resamples whole calendar days (ADR-0048)."""
    _within("day_boxed:martingale-rho0.5", "beats_null")


def test_position_boxed_null_holds_size_on_empty_world():
    """The review's F01: a world with nothing in it, and a guard that passed it fourteen times in a hundred. Within
    tolerance since M16.14 draws at the winner's count (ADR-0048)."""
    _within("position_boxed:martingale-rho0.0", "beats_null")


SHARED_MARKET = ("position_boxed:martingale-rho0.5-farstop", "position_boxed:martingale-rho0.5")
OPEN_AT_005 = ("an open residual (ADR-0048, *As built*): on names that share a market the multi-day engine's beats-null passes a world "
               "with nothing in it 0.095 and 0.100 of the time at a declared 0.05 over these two hundred seeds — it was 0.340 — and "
               "0.067 over a thousand, against a tolerance of 0.066 there. At 0.01 it is at its declared rate")


@pytest.mark.parametrize("world", SHARED_MARKET)
def test_position_boxed_null_holds_size_under_common_factor_at_the_alpha_the_guards_run_at(world):
    """Both defects at once: 0.295 as built at a declared 0.01, at its declared rate since M16.14 — where the stop
    cannot bind, so that long mirrors short and a coin's side is exactly the null, and where it can."""
    _within(world, "beats_null", alphas=(0.01,))


@pytest.mark.parametrize("world", SHARED_MARKET)
@pytest.mark.xfail(strict=True, reason=OPEN_AT_005)
def test_position_boxed_null_holds_size_under_common_factor_at_005(world):
    _within(world, "beats_null", alphas=(0.05,))


def test_fifth_check_holds_size_for_a_long_entry_with_no_timing_skill():
    """The fifth check's own control: on a rising market a long entry with no timing skill is refused."""
    _within("day_boxed:updrift-rho0.5", "beats_always_long")


def test_fifth_check_holds_size_on_empty_world_position_boxed():
    """The fifth check's copy of F01: always-long was resampled at its own count, not the winner's — 0.055 and 0.165 as
    built, within tolerance since M16.15 resamples winner and baseline together by calendar day (ADR-0049)."""
    _within("position_boxed:martingale-rho0.0", "beats_always_long")


def test_fifth_check_refuses_a_long_entry_with_no_skill_where_the_stop_binds():
    """Where the stop bites a short harder than a long, a long entry with no skill is ahead of a coin's side — and
    beats-null says so, one time in ten at 0.05. Refusing it is this check's work, and it does."""
    _within("position_boxed:martingale-rho0.5", "beats_always_long")


def test_fifth_check_refuses_coin_flip_on_drifting_paths():
    """The review's F04: on a market that falls, a coin flip passed the check that is meant to attest the entry 96
    times in 100, by being short half the time. Its baseline is now the coin's own expectation (ADR-0049)."""
    _within("day_boxed:downdrift-rho0.0:coin", "beats_always_long")


def test_fifth_check_power_on_planted_reversal():
    """And it still sees what is there: the signal control's planted reversal passes it at the control's own corrected
    alpha at no less than the planned rate, less tolerance."""
    _within("controls:signal", "beats_always_long")


def test_every_row_of_the_table_is_a_test_here():
    """A row added to the table without a test would be printed and never enforced."""
    import inspect

    source = inspect.getsource(inspect.getmodule(test_every_row_of_the_table_is_a_test_here))
    for r in ROWS:
        assert f'_within("{r.key}", "{r.guard}"' in source or (r.key in SHARED_MARKET and r.guard == "beats_null"), (r.key, r.guard)
        assert r.kind in ("size", "power") and r.seeds >= (calibrate.SIZE_SEEDS if r.kind == "size" else calibrate.POWER_SEEDS)
