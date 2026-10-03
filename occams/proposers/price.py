"""The price_daily proposer: a mechanism on daily bars alone, no regime
gate, on the M0.7 class (F12, M7.6 sibling). Every number it emits is its
own declaration; alpha is the accountant's (R4.4); a human confirms the
registration (M8.1) — this module never writes a record.

Six mechanisms, one per entry kind the closed spec enum offers on daily
bars — three from M3.2 and three added by decision in ADR-0037 (reversal
after a streak, reversal after a decline of size, reversal conditioned on
trend). Each is stated with both interpretations and a falsifier, so a
null is a result and not an excuse:

* ``close_below_ma`` — short-horizon reversal: after a close below its
  moving average, an index ETF's next few days over-correct the selling.
* ``close_above_ma`` — trend persistence: after a close above its moving
  average, the next bars continue, because participants under-react.
* ``breakout_high`` — breakout continuation without a regime gate, held
  for more than one bar: Q-003/Q-004's mechanism with the gate removed
  and the hold lengthened.
"""

from __future__ import annotations

from occams.config import InformationAxis
from occams.hypothesis import Gates
from occams.measurement import Floor
from occams.proposers.base import Draft, Proposer, Sandbox, Sweep
from occams.spec.spec import (Capability, Entry, EntryKind, Exit, ExitKind, Horizon, OrderType, Side, Sizing, Stop,
                              StopKind, StrategySpec, UniverseRule)

PRICE_ENTRIES = (EntryKind.CLOSE_BELOW_MA, EntryKind.CLOSE_ABOVE_MA, EntryKind.BREAKOUT_HIGH, EntryKind.BREAKOUT_LOW,
                 EntryKind.DOWN_RUN, EntryKind.RETURN_BELOW, EntryKind.PULLBACK_IN_TREND)   # the last three: ADR-0037
PARAMS = {EntryKind.CLOSE_BELOW_MA: ("lookback",), EntryKind.CLOSE_ABOVE_MA: ("lookback",),
          EntryKind.BREAKOUT_HIGH: ("lookback",), EntryKind.BREAKOUT_LOW: ("lookback",), EntryKind.DOWN_RUN: ("runs",),
          EntryKind.RETURN_BELOW: ("lookback", "percent"), EntryKind.PULLBACK_IN_TREND: ("short", "long")}
SUBJECT = "a liquid US index ETF"   # the first programme's class; a survey fills in its universe's own subject (M12.2)

MECHANISM = {
    EntryKind.CLOSE_BELOW_MA: (
        "After a close below its {lookback}-bar moving average, {subject} carries positive EV in net R "
        "over the next {hold} bars because short-horizon selling overshoots and is corrected (short-term reversal)",
        "the winner cell clears the declared floor and beats random entry at the corrected alpha: the reversal is real after costs",
        "the days after a close below the average are not distinguishable from random entry after costs: no reversal to trade",
    ),
    EntryKind.CLOSE_ABOVE_MA: (
        "After a close above its {lookback}-bar moving average, {subject} carries positive EV in net R "
        "over the next {hold} bars because participants under-react and the move persists (trend persistence)",
        "the winner cell clears the declared floor and beats random entry at the corrected alpha: persistence is real after costs",
        "the days after a close above the average are not distinguishable from random entry after costs: no persistence to trade",
    ),
    EntryKind.BREAKOUT_HIGH: (
        "A buy-stop at the highest high of the prior {lookback} bars, held for {hold} bars, carries "
        "positive EV in net R on {subject} because new highs are under-reacted to (breakout continuation)",
        "the winner cell clears the declared floor and beats random entry at the corrected alpha: continuation outlives the entry day",
        "a longer hold does not rescue breakout continuation: not distinguishable from random entry after costs",
    ),
    EntryKind.BREAKOUT_LOW: (
        "A buy-limit at the lowest low of the prior {lookback} bars, held for {hold} bars, carries "
        "positive EV in net R on {subject} because a fall to a new low is over-sold and bought back (reversal at a new low)",
        "the winner cell clears the declared floor and beats random entry at the corrected alpha: the new-low reversal is real after costs",
        "buying a new low is not distinguishable from random entry after costs: no reversal at the low to trade",
    ),
    EntryKind.DOWN_RUN: (
        "After {runs} consecutive lower closes, {subject} carries positive EV in net R over the next {hold} bars "
        "because a streak of declines exhausts short-horizon sellers and the next days correct (reversal after a streak; ADR-0037)",
        "the winner cell clears the declared floor and beats random entry at the corrected alpha: the streak reversal is real after costs",
        "the days after a streak of declines are not distinguishable from random entry after costs: streaks carry no reversal to trade",
    ),
    EntryKind.RETURN_BELOW: (
        "After a decline of at least {percent} % over {lookback} bars, {subject} carries positive EV in net R over the "
        "next {hold} bars because a fall of that size over-corrects (reversal after a decline of size; ADR-0037)",
        "the winner cell clears the declared floor and beats random entry at the corrected alpha: the over-correction is real after costs",
        "the days after a decline of that size are not distinguishable from random entry after costs: magnitude carries no reversal to trade",
    ),
    EntryKind.PULLBACK_IN_TREND: (
        "After a close below its {short}-bar average while above its {long}-bar average, {subject} carries positive EV in "
        "net R over the next {hold} bars because a dip inside an uptrend is bought back (reversal conditioned on trend; ADR-0037)",
        "the winner cell clears the declared floor and beats random entry at the corrected alpha: the pullback is bought back after costs",
        "a dip inside an uptrend is not distinguishable from random entry after costs: the trend adds no reversal to trade",
    ),
}


def entry_params(entry: EntryKind, **given) -> tuple[tuple[str, float], ...]:
    """The entry's declared parameters, in the kind's own order; a missing
    or extra one is refused by name — there is no default for a mechanism's
    parameters."""
    if entry not in PRICE_ENTRIES:
        raise ValueError(f"{entry.value} is not a price_daily entry; one of {[e.value for e in PRICE_ENTRIES]}")
    names = PARAMS[entry]
    missing = [n for n in names if given.get(n) is None]
    extra = [n for n, v in given.items() if v is not None and n not in names]
    if missing or extra:
        raise ValueError(f"{entry.value} declares {list(names)}; missing {missing}, not its own {extra}")
    return tuple((n, float(given[n])) for n in names)


def mechanism_sentence(entry: EntryKind, *, hold: int, subject: str = SUBJECT, **params) -> str:
    """The mechanism hypothesis in the proposer's words with the numbers and
    the subject filled in — the sentence a survey cell carries (M12.2)."""
    p = dict(entry_params(entry, **params))
    return MECHANISM[entry][0].format(hold=int(hold), subject=subject,
                                      **{k: (int(v) if float(v).is_integer() else v) for k, v in p.items()})


def price_template(entry: EntryKind, *, hold_bars: int, stop_percent: float = 3.0,
                   horizon: Horizon = Horizon.MULTI_DAY, **params) -> StrategySpec:
    """A long-only daily-bar spec with a time exit; the sweep edits the stop
    (and the hold, if declared as an axis). A breakout above enters on a
    resting stop order, a breakout below on a resting limit, and both
    declare that they rest; every other kind is a market order on the next
    open and declares only the native stop."""
    breakout = entry in (EntryKind.BREAKOUT_HIGH, EntryKind.BREAKOUT_LOW)
    return StrategySpec(
        entries=(Entry(entry, Side.LONG, entry_params(entry, **params)),),
        exits=(Exit(ExitKind.TIME, (("bars", hold_bars),)),),
        stop=Stop(StopKind.PERCENT, stop_percent), sizing=Sizing(),
        order_type=(OrderType.STOP if entry is EntryKind.BREAKOUT_HIGH else OrderType.LIMIT if breakout else OrderType.MARKET),
        horizon=horizon, universe=UniverseRule((("venue", "NYSE"), ("class", "us_large"))),
        required_capabilities=frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS} if breakout
                                        else {Capability.NATIVE_STOP}),
        axis=InformationAxis.PRICE_DAILY, regime=None)


class PriceProposer(Proposer):
    """Drafts one mechanism question per entry kind on daily bars. It sees
    the definition partition through ``precommit`` and nothing else."""

    name = "price"

    def __init__(self, *, entry: EntryKind, hold_bars: int, floor: Floor, sigma_r: float,
                 sigma_provenance: str, power: float, gates: Gates, sweep: Sweep, **params):
        self.params = dict(entry_params(entry, **params))
        self.entry, self.hold_bars = entry, int(hold_bars)
        self.floor, self.sigma_r, self.sigma_provenance = floor, sigma_r, sigma_provenance
        self.power, self.gates, self.sweep = power, gates, sweep

    def propose(self, sandbox: Sandbox, *, sources: tuple[str, ...] = ()) -> tuple[Draft, ...]:
        refs, surfaced = [], []
        for url in sources:
            q = sandbox.retrieve(url)
            refs.append(q.reference)
            surfaced.extend(f"{q.reference}: {line}" for line in q.flagged)
        _mechanism, if_true, if_false = MECHANISM[self.entry]
        d = Draft(
            proposer=self.name, axis=InformationAxis.PRICE_DAILY,
            mechanism=mechanism_sentence(self.entry, hold=self.hold_bars, **self.params),
            if_true=if_true, if_false=if_false,
            falsifier="the winner cell's EV in net R at or below the null's corrected quantile, or below the floor",
            floor=self.floor, sweep=self.sweep, sigma_r=self.sigma_r, sigma_provenance=self.sigma_provenance,
            power=self.power, gates=self.gates, sources=tuple(refs), surfaced=tuple(surfaced),
            notes=f"entry={self.entry.value}; " + "; ".join(f"{k}={v:g}" for k, v in self.params.items())
                  + f"; hold={self.hold_bars}; no regime gate")
        return (d,)
