"""FX conversion spread is a cost; FX drift is not (D25, ADR-0026, M5.3,
M5.4). Net R is measured in the instrument's currency and divided by
planned R converted at entry, so the rate's later movement cannot enter
it. The movement is an exposure: reported separately, in money, against
the configured limit — and money lives in Operations, never the Register.
"""

from __future__ import annotations

from dataclasses import dataclass

from occams.register import Money


@dataclass(frozen=True)
class FxAtEntry:
    """Units of instrument currency per unit of account currency, at entry."""

    rate: float

    def risk_in_instrument(self, risk_account: float) -> float:
        return risk_account * self.rate


def net_r_instrument(*, pnl_instrument: float, costs_instrument: float, risk_account: float,
                     fx_entry: FxAtEntry) -> float:
    """Everything in the instrument's currency; R converted once, at entry."""
    r_instr = fx_entry.risk_in_instrument(risk_account)
    if r_instr <= 0:
        raise ValueError("planned risk must be positive")
    return (pnl_instrument - costs_instrument) / r_instr


def drift_exposure(*, position_value_instrument: float, fx_entry: float, fx_now: float,
                   account_currency: str) -> Money:
    """The account-currency value of holding instrument currency: what the
    rate did since entry, in money. Never in net R."""
    if fx_entry <= 0 or fx_now <= 0:
        raise ValueError("rates must be positive")
    return Money(position_value_instrument / fx_now - position_value_instrument / fx_entry, account_currency)


@dataclass(frozen=True)
class FxExposure:
    """A money projection line: open foreign-currency value against the
    configured limit (Operations-side)."""

    open_value_account: Money
    limit_account: Money

    @property
    def within_limit(self) -> bool:
        assert self.open_value_account.currency == self.limit_account.currency
        return abs(self.open_value_account.amount) <= self.limit_account.amount


def exposure_against_limit(*, open_value_instrument: float, fx_now: float, limit_account: float,
                           account_currency: str) -> FxExposure:
    return FxExposure(Money(open_value_instrument / fx_now, account_currency), Money(limit_account, account_currency))
