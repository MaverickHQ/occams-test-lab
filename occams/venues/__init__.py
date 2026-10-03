"""Venues (F13): a port, swappable. A venue places orders and reports
placements; its ``kind`` says what its fills can evidence. ``paper`` keeps
CI offline and satisfies the port contract; ``proposal`` renders a card and
a human places the order (R1.7); ``live`` arrives at M10.9 behind the
LiveGate."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from occams.register import Money


@dataclass(frozen=True)
class OrderRequest:
    spec_hash: str
    instrument: str
    side: str          # buy | sell
    order_type: str    # market | limit | stop | stop_limit
    level: float | None
    quantity: float
    stop_level: float
    size: Money        # planned risk at minimum size (config), never in the Register


@dataclass(frozen=True)
class Placement:
    venue_kind: str
    placement_id: str
    status: str        # pending | filled | rejected
    fill_price: float | None = None
    note: str = ""


class Venue(Protocol):
    kind: str

    def place(self, request: OrderRequest) -> Placement: ...
