"""The forward runner (M9.4, M9.4b, M9.5, M9.6, M9.8).

Opens a declared window on a venue that can evidence cost and obtainability
— the proposal venue by default; the paper venue is refused by name — and
then, day by day on data unseen at measurement, lets the compiled spec
decide, renders a card from that decision, and records what the human
reports back. An acknowledgement logs a fill; it cannot change the
decision. The window is evaluated once. A pass is recorded with the one
sentence it is allowed to say.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from occams.cards import Acknowledgement, Decision
from occams.data.instants import instant
from occams.engine.day_boxed import signal, stop_distance
from occams.forward.window import ForwardWindow, Resolution, evaluate
from occams.guards import Refusal, refuse_or_pass
from occams.register import Money, Operations, Register
from occams.sizing import position_size
from occams.spec.compile import CompiledStrategy
from occams.spec.spec import ExitKind, Side


class ForwardRefused(RuntimeError):
    pass


@dataclass
class ForwardRun:
    compiled: CompiledStrategy
    window: ForwardWindow
    venue: object
    register: Register
    operations: Operations
    min_size: Money
    hypothesis_id: str | None
    opened_at: datetime
    fills: list[tuple[Decision, Acknowledgement]] = field(default_factory=list)
    defects: list[str] = field(default_factory=list)
    resolution: Resolution | None = None
    slippage_bound: float = 0.0  # a fill worse than the decision by more than this is an obtainability defect
    regime: object = None        # the frozen classifier's context, required for a gated spec

    @property
    def trades(self) -> int:
        return len(self.fills)


def open_window(compiled: CompiledStrategy, window: ForwardWindow, *, venue, register: Register,
                operations: Operations, min_size: Money, hypothesis_id: str | None, now: datetime,
                slippage_bound: float = 0.0, regime=None) -> ForwardRun:
    from occams.engine.regime_gate import check_gate

    check_gate(compiled.spec.regime, regime)  # a gated spec never decides without its classifier
    if getattr(venue, "kind", None) == "paper":
        r = Refusal("MEASURED->FORWARD", "a forward window wired to the paper venue is refused: a simulator cannot "
                    "evidence cost or obtainability — it answers with the assumptions under test (ADR-0032)",
                    {"venue_kind": "paper"})
        refuse_or_pass(r, register, spec_hash=compiled.spec_hash, hypothesis_id=hypothesis_id)
    if getattr(venue, "kind", None) not in ("proposal", "live"):
        raise ForwardRefused(f"unknown venue kind {getattr(venue, 'kind', None)!r}")
    if min_size.amount <= 0:
        raise ForwardRefused("the forward window trades at the configured minimum size, which must be positive (M0.13)")
    opened = instant(now)
    register.append(register.ForwardWindowOpened(compiled.spec_hash, hypothesis_id, window.min_trades,
                                                 window.max_duration_days, opened.isoformat(), venue.kind))
    return ForwardRun(compiled, window, venue, register, operations, min_size, hypothesis_id, opened,
                      slippage_bound=slippage_bound, regime=regime)


def decide(run: ForwardRun, bars, day: int, *, at: datetime) -> Decision | None:
    """The engine's decision for today's box, from bars strictly before it."""
    first = bars.day.index(day)
    if first == 0:
        return None
    spec = run.compiled.spec
    from occams.engine.regime_gate import admits

    if not admits(spec.regime, run.regime, bars, first):
        return None
    for entry in spec.entries:
        fired, side, level = signal(entry, bars, first)
        if fired:
            ref = bars.close[first - 1] if level is None else level
            dist = stop_distance(spec, bars, first, ref)
            stop = ref - dist if side is Side.LONG else ref + dist
            target = None
            for x in spec.exits:
                if x.kind is ExitKind.TARGET_R:
                    m = x.param("multiple")
                    target = ref + m * dist if side is Side.LONG else ref - m * dist
            qty = position_size(risk_account=run.min_size.amount, fx_instrument_per_account=1.0, stop_distance_instrument=dist)
            return Decision(run.compiled.spec_hash, bars.name, side, spec.order_type.value, level, stop, dist, qty,
                            instant(at).isoformat(), day, target)
    return None


def step(run: ForwardRun, bars_by_name, day: int, *, at: datetime, acknowledge) -> list[Decision]:
    """One day: propose, collect acknowledgements, log fills and exposures.
    ``acknowledge(decision, bars)`` is the human — or the replay policy."""
    if run.resolution is not None:
        raise ForwardRefused("the window has been evaluated; a second run is a new Hypothesis")
    decided: list[Decision] = []
    for name in sorted(bars_by_name):
        bars = bars_by_name[name]
        if day not in bars.day:
            continue
        d = decide(run, bars, day, at=at)
        if d is None:
            continue
        decided.append(d)
        run.venue.propose(d)
        run.operations.append(run.operations.ProposalIssued(d.spec_hash, d.card_id, d.instrument,
                                                            d.side.value, d.quantity, run.min_size))
        ack = acknowledge(d, bars)
        if ack is None or ack.fill_price is None:
            run.venue.pending.pop(d.card_id, None)
            continue
        unchanged = run.venue.acknowledge(ack)
        assert unchanged == d  # an acknowledgement is never a veto (M9.8)
        run.operations.append(run.operations.ForwardFill(d.spec_hash, d.card_id, d.instrument, ack.fill_price,
                                                         d.quantity, run.min_size, ack.by, ack.acknowledged_at))
        run.operations.append(run.operations.Exposure(d.spec_hash, d.instrument, d.quantity, run.min_size,
                                                      ack.acknowledged_at))
        run.fills.append((d, ack))
        ref = d.level if d.level is not None else bars.open[bars.day.index(day)]
        adverse = (ack.fill_price - ref) if d.side is Side.LONG else (ref - ack.fill_price)
        if adverse > run.slippage_bound + 1e-12:
            run.defects.append(f"obtainability: {d.instrument} box {day} filled {ack.fill_price} against {ref} "
                               f"({adverse:.4f} adverse, bound {run.slippage_bound})")
    return decided


def resolve(run: ForwardRun, *, now: datetime) -> Resolution | None:
    """Evaluate once. Returns None when not yet due."""
    if run.resolution is not None:
        raise ForwardRefused("the window has already been evaluated once; there is no second look")
    elapsed = (instant(now) - run.opened_at).days
    res = evaluate(run.window, trades=run.trades, days_elapsed=elapsed, defects=tuple(run.defects))
    if res is None:
        return None
    run.resolution = res
    run.register.append(run.register.ForwardWindowResolved(run.compiled.spec_hash, run.hypothesis_id,
                                                           res.outcome.value, res.statement, res.trades,
                                                           res.days_elapsed, res.defects))
    return res
