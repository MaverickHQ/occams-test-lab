"""The regime gate the engines read (F11, M7.6, ADR-0005, ADR-0007).

A gated spec trades only on boxes the frozen classifier labels with its
regime. The label for a box is computed from bars **strictly before** the
box — at index level from the index series on the same calendar day, at
instrument level from the name's own bars — so the gate is causal by the
same construction the classifier's own causality test enforces.

The context is built from the Register's ``ClassifierFrozen`` record and
the archive: the engine refuses to run a gated spec without it, and refuses
a context whose frozen hash is not the one the spec names (D2).
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass

from occams.data.bars import Bars
from occams.spec.spec import Regime, RegimeGate


class GateRefusal(RuntimeError):
    pass


@dataclass(frozen=True)
class RegimeContext:
    classifier: object          # occams.proposers.regime.RegimeClassifier
    index_name: str
    index_bars: Bars | None     # required at index level

    @property
    def frozen_hash(self) -> str:
        return self.classifier.frozen_hash

    @classmethod
    def from_register(cls, register, archive) -> RegimeContext | None:
        from occams.proposers.regime import ClusterLevel, frozen

        clf = frozen(register)
        if clf is None:
            return None
        rows = [r for r in register.records() if r["type"] == "ClassifierFrozen"]
        index_name = rows[-1]["index_name"]
        index_bars = None
        if clf.level is ClusterLevel.INDEX:
            try:
                latest = archive.latest_bars(names=(index_name,))     # M14.7: the index alone; a survey box may hold nothing else
            except Exception:   # noqa: BLE001 — NotArchived, or a wrapper without the name: the same refusal either way
                latest = {}
            if index_name not in latest:
                raise GateRefusal(f"the frozen classifier labels {index_name!r} at index level, and the archive does not hold it")
            index_bars = latest[index_name][0]
        return cls(clf, index_name, index_bars)

    def _index_bar_for(self, bars: Bars, first: int) -> int | None:
        """The index bar whose label the box at ``first`` reads: the bar on the
        same calendar day, or the one after the last bar before it (a gap day)."""
        day = bars.day[first]
        i = bisect_right(self.index_bars.day, day) - 1
        if i < 0:
            return None
        return i if self.index_bars.day[i] == day else i + 1

    def label_for(self, bars: Bars, first: int) -> Regime | None:
        """The regime in force for the box beginning at ``first`` of ``bars``."""
        from occams.proposers.regime import ClusterLevel

        if self.classifier.level is ClusterLevel.INSTRUMENT or self.index_bars is None:
            return self.classifier.label_at(bars, first)
        i = self._index_bar_for(bars, first)
        if i is None:
            return None
        return self.classifier.label_at(self.index_bars, i)      # reads index closes strictly before bar i

    def known_at_for(self, bars: Bars, first: int):
        """M4.11 (ADR-0020, D10): the instant the label for the box at ``first``
        became known — the close of the last index bar it read — when the
        index carries instants. None at instrument level, or without them."""
        from occams.proposers.regime import ClusterLevel

        if self.classifier.level is ClusterLevel.INSTRUMENT or self.index_bars is None or self.index_bars.close_at is None:
            return None
        i = self._index_bar_for(bars, first)
        if i is None or i - 1 < 0:
            return None
        return _close_instant(self.index_bars.close_at[min(i - 1, len(self.index_bars.close_at) - 1)])


def check_gate(gate: RegimeGate | None, ctx: RegimeContext | None) -> None:
    if gate is None:
        return
    if ctx is None:
        raise GateRefusal("a regime-gated spec cannot run without the frozen classifier's context (ADR-0005)")
    if ctx.frozen_hash != gate.classifier_hash:
        raise GateRefusal(f"the spec names classifier {gate.classifier_hash[:12]}; the context holds "
                          f"{ctx.frozen_hash[:12]} — the frozen classifier referenced is the one used (D2)")
    if ctx.index_name != gate.index_name:
        raise GateRefusal(f"the spec labels {gate.index_name!r} at index level; the context labels {ctx.index_name!r}")


def _close_instant(s: str):
    from datetime import datetime

    from occams.data.instants import instant

    return instant(datetime.fromisoformat(s))


def admits(gate: RegimeGate | None, ctx: RegimeContext | None, bars: Bars, first: int) -> bool:
    """Whether the box at ``first`` is inside the gate's regime — and, when
    both the name's bars and the index carry instants, whether the label
    was known before the name's bar closed (M4.11): a label known between
    two venues' closes admits the later venue's bar and refuses the
    earlier's, whatever the ordinals say (ADR-0020)."""
    if gate is None:
        return True
    if ctx.label_for(bars, first) is not gate.label:
        return False
    known = ctx.known_at_for(bars, first)
    if known is not None and bars.close_at is not None:
        from occams.data.instants import usable

        return usable(_close_instant(bars.close_at[first]), known)
    return True
