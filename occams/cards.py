"""The proposal card, generated from the spec and the engine's decision
(F9, R8, M9.7). There is no hand-written text about what to do: every line
is a field of the ``Decision`` the engine emitted, so a card can only say
what the engine decided. Acknowledging a card records that a human acted;
it cannot change the decision (M9.8)."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from occams.spec.spec import Side


@dataclass(frozen=True)
class Decision:
    """What the engine decided for one box: the whole content of a card."""

    spec_hash: str
    instrument: str
    side: Side
    order_type: str
    level: float | None
    stop_level: float
    stop_distance: float
    quantity: float
    decided_at: str      # UTC instant
    box_day: int
    target_level: float | None = None

    @property
    def card_id(self) -> str:
        return hashlib.sha256(f"{self.spec_hash}|{self.instrument}|{self.box_day}|{self.decided_at}".encode()).hexdigest()[:16]


def render(d: Decision) -> str:
    """Text from fields. The wording of the last line is pinned by test (M9.6)."""
    action = "BUY" if d.side is Side.LONG else "SELL"
    level = "at the open (market)" if d.level is None else f"{d.order_type} at {d.level:.4f}"
    lines = [
        f"*Occams proposal* `{d.card_id}`",
        f"spec `{d.spec_hash[:12]}` · {d.instrument} · box {d.box_day}",
        f"{action} {d.quantity:g} — {level}",
        f"protective stop {d.stop_level:.4f} (distance {d.stop_distance:.4f})",
    ]
    if d.target_level is not None:
        lines.append(f"target {d.target_level:.4f}")
    lines += [f"decided {d.decided_at}",
              "Reply with the fill to acknowledge. Acknowledgement records what you did; it does not change the decision."]
    return "\n".join(lines)


@dataclass(frozen=True)
class Acknowledgement:
    """A human saw the card and reports what happened. Takes no decision
    fields, so there is nothing here that could alter one."""

    card_id: str
    by: str
    fill_price: float | None   # None = not placed
    acknowledged_at: str
