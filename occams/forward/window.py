"""The window, declared as a pair, resolving three ways (ADR-0023, M9.5),
and the sentence a pass is allowed to say (M9.6)."""

from __future__ import annotations

import enum
from dataclasses import dataclass


class Outcome(enum.Enum):
    PASS = "pass"
    REJECTED = "rejected"
    FREQUENCY_FAILURE = "frequency_failure"


PASS_STATEMENT = ("no implementation, cost or obtainability defect was found; "
                  "the edge is not confirmed")
REJECTED_STATEMENT = "forward behaviour inconsistent with the backtest"
FREQUENCY_STATEMENT = ("too few trades at the deadline: the frequency half of the "
                       "declared floor failed, measured forward")


@dataclass(frozen=True)
class ForwardWindow:
    min_trades: int
    max_duration_days: int

    def __post_init__(self):
        if self.min_trades < 1 or self.max_duration_days < 1:
            raise ValueError("a window needs at least one trade and one day — a zero-trade window is the vacuous pass")


@dataclass(frozen=True)
class Resolution:
    outcome: Outcome
    statement: str
    trades: int
    days_elapsed: int
    defects: tuple[str, ...]


def evaluate(window: ForwardWindow, *, trades: int, days_elapsed: int, defects: tuple[str, ...]) -> Resolution | None:
    """None means not yet due. Evaluated once by the runner."""
    if trades >= window.min_trades:
        if defects:
            return Resolution(Outcome.REJECTED, REJECTED_STATEMENT, trades, days_elapsed, tuple(defects))
        return Resolution(Outcome.PASS, PASS_STATEMENT, trades, days_elapsed, ())
    if days_elapsed >= window.max_duration_days:
        return Resolution(Outcome.FREQUENCY_FAILURE, FREQUENCY_STATEMENT, trades, days_elapsed, tuple(defects))
    return None
