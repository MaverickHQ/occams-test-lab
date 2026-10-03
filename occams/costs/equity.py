"""``costs/equity.py`` — spread, taxes and levies, FX conversion (M5.1).
Shares no field with the donor's futures ``Costs``: there is no multiplier,
no tick, no per-contract commission here.

Two kinds of number live in this module and they are kept apart.
**Published components** are facts with provenance — the venue's help
centre pages read on 2026-09-10 (docs/M0-ANSWERS.md §M0.2). **The spread**
is not published: it is a *declared range* until M5.0 measures it on the
demo account, and the model says which it is holding. ``bound()`` takes the
worst end of the range, which is what approval uses (D23); ``measured``
becomes true only when observations with provenance are supplied.

``cost_in_r = c / s``: the round-trip cost as a fraction of notional over
the stop distance as a fraction of price — M0.16's identity.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, replace
from statistics import fmean


class InstrumentClass(enum.Enum):
    LSE_SHARE = "lse_share"          # SDRT on purchase
    LSE_ETF_GBP = "lse_etf_gbp"      # no SDRT, no FX from a GBP account
    US_LARGE = "us_large"            # US-listed ETF or large cap — the M0.7 class
    EU_SHARE = "eu_share"            # Xetra / Euronext


PROVENANCE_M02 = ("the M0 venue's help-centre fee articles, accessed 2026-09-10 and quoted in "
                  "docs/M0-ANSWERS.md §M0.2")


@dataclass(frozen=True)
class Published:
    """Fees and taxes the venue and the tax authorities publish."""

    stamp_duty_buy_lse_share: float = 0.005        # SDRT 0.5 % on LSE share purchases; none on ETFs
    fx_conversion_per_leg: float = 0.0015          # 0.15 % per conversion; two legs when currencies differ
    ptm_levy_gbp_per_side: float = 1.50            # on orders over £10,000, purchase and sale
    ptm_threshold_gbp: float = 10_000.0
    sec_fee_sell_fraction: float = 0.0000206       # "$0.00206%" of the sale, negligible on either reading
    finra_taf_per_share_sold: float = 0.000195     # USD per share sold
    french_ftt_buy: float = 0.004                  # large French names only; EU_SHARE carries it as the bound
    provenance: str = PROVENANCE_M02


PUBLISHED = Published()

# The M0.2 declared spread ranges (fraction of price, full spread crossed once
# per round trip). Not measurements. M5.0 replaces them.
DECLARED_SPREAD: dict[InstrumentClass, tuple[float, float]] = {
    InstrumentClass.US_LARGE: (0.0002, 0.0010),
    InstrumentClass.LSE_ETF_GBP: (0.0005, 0.0020),
    InstrumentClass.LSE_SHARE: (0.0005, 0.0015),   # FTSE 100 names; FTSE 250 is 0.20-0.60 %
    InstrumentClass.EU_SHARE: (0.0005, 0.0020),
}
DECLARED_PROVENANCE = "docs/M0-ANSWERS.md §M0.2 — declared range; M5.0 measurement on the demo account pending"


@dataclass(frozen=True)
class SpreadObservation:
    """One reading from the demo account (M5.0): the author's action."""

    instrument: str
    at: str          # UTC instant
    bid: float
    ask: float
    phase: str       # open | mid | close

    @property
    def fraction(self) -> float:
        mid = (self.bid + self.ask) / 2
        return (self.ask - self.bid) / mid


@dataclass(frozen=True)
class Spread:
    fraction: float
    basis: str          # "declared" | "bounded" | "measured"
    provenance: str
    observations: int = 0


def measured_spread(observations: tuple[SpreadObservation, ...], *, provenance: str) -> Spread:
    """A measured spread needs the open, mid-session and close phases covered
    (M5.0's Done-when) — otherwise it is a partial reading, not a measurement."""
    if not observations:
        raise ValueError("no observations")
    phases = {o.phase for o in observations}
    if not {"open", "mid", "close"} <= phases:
        raise ValueError(f"measurement needs open, mid and close phases; got {sorted(phases)}")
    return Spread(fmean(o.fraction for o in observations), "measured", provenance, len(observations))


class NotMeasured(RuntimeError):
    pass


@dataclass(frozen=True)
class EquityCosts:
    instrument_class: InstrumentClass
    instrument_currency: str
    account_currency: str
    spread: Spread
    published: Published = PUBLISHED

    @classmethod
    def declared(cls, instrument_class: InstrumentClass, *, instrument_currency: str, account_currency: str,
                 low: bool = False) -> "EquityCosts":
        lo, hi = DECLARED_SPREAD[instrument_class]
        return cls(instrument_class, instrument_currency, account_currency,
                   Spread(lo if low else hi, "declared", DECLARED_PROVENANCE))

    def bound(self) -> "EquityCosts":
        """The conservative bound approval uses (D23): the worst end of the
        declared range. A measured spread is already a fact and stays."""
        if self.spread.basis == "measured":
            return self
        _, hi = DECLARED_SPREAD[self.instrument_class]
        return replace(self, spread=Spread(hi, "bounded", DECLARED_PROVENANCE))

    def with_measured(self, observations: tuple[SpreadObservation, ...], *, provenance: str) -> "EquityCosts":
        return replace(self, spread=measured_spread(observations, provenance=provenance))

    @property
    def basis(self) -> str:
        return self.spread.basis

    @property
    def converts(self) -> bool:
        return self.instrument_currency != self.account_currency

    # ---- the components, as fractions of notional per round trip ----------

    def fixed_fraction(self) -> float:
        p = self.published
        c = 0.0
        if self.instrument_class is InstrumentClass.LSE_SHARE:
            c += p.stamp_duty_buy_lse_share
        if self.instrument_class is InstrumentClass.EU_SHARE:
            c += p.french_ftt_buy
        if self.instrument_class is InstrumentClass.US_LARGE:
            c += p.sec_fee_sell_fraction
        if self.converts:
            c += 2 * p.fx_conversion_per_leg
        return c

    def round_trip_fraction(self, *, notional_gbp: float | None = None) -> float:
        c = self.fixed_fraction() + self.spread.fraction
        if notional_gbp is not None and notional_gbp > self.published.ptm_threshold_gbp \
                and self.instrument_class in (InstrumentClass.LSE_SHARE, InstrumentClass.LSE_ETF_GBP):
            c += 2 * self.published.ptm_levy_gbp_per_side / notional_gbp
        return c

    def cost_in_r(self, *, entry_price: float, stop_distance: float, notional_gbp: float | None = None) -> float:
        """``c / s`` (M0.16): cost as a fraction of notional over the stop as
        a fraction of price. Independent of account currency except through
        the conversion legs, which are a cost, never a drift."""
        if entry_price <= 0 or stop_distance <= 0:
            raise ValueError("entry price and stop distance must be positive")
        return self.round_trip_fraction(notional_gbp=notional_gbp) * entry_price / stop_distance


def net_r(gross_r: float, cost_in_r: float) -> float:
    return gross_r - cost_in_r
