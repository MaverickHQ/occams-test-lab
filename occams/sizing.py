"""R is planned risk, fixed in account currency; size is R over stop
distance, both in instrument currency (D5, ADR-0003). Results are multiples
of planned R, so a gap through the stop records worse than -1R (M3.8)."""

from __future__ import annotations

from occams.spec.spec import Side


def position_size(*, risk_account: float, fx_instrument_per_account: float,
                  stop_distance_instrument: float) -> float:
    """Shares (or units) for planned risk ``risk_account`` in the account
    currency, converted at entry by ``fx_instrument_per_account`` (units of
    instrument currency per unit of account currency)."""
    if risk_account <= 0 or fx_instrument_per_account <= 0 or stop_distance_instrument <= 0:
        raise ValueError("risk, FX rate and stop distance must all be positive")
    return (risk_account * fx_instrument_per_account) / stop_distance_instrument


def r_multiple(*, entry: float, exit: float, stop_distance: float, side: Side) -> float:
    """Realised result as a multiple of PLANNED R. Not clipped at -1."""
    if stop_distance <= 0:
        raise ValueError("stop distance must be positive")
    direction = 1.0 if side is Side.LONG else -1.0
    return (exit - entry) * direction / stop_distance
