"""The proposal venue (R1.7, ADR-0032): the card is sent, a human places
the order by hand, and the acknowledgement carries the fill back. The venue
holds no credentials and places nothing itself."""

from __future__ import annotations

from dataclasses import dataclass, field

from occams.cards import Acknowledgement, Decision, render
from occams.telegram import Transport
from occams.venues import OrderRequest, Placement


@dataclass
class ProposalVenue:
    transport: Transport
    kind: str = "proposal"
    pending: dict[str, Decision] = field(default_factory=dict)
    sent: dict[str, str] = field(default_factory=dict)

    def propose(self, d: Decision) -> str:
        msg = self.transport.send(render(d))
        self.pending[d.card_id] = d
        self.sent[d.card_id] = msg
        return d.card_id

    def place(self, request: OrderRequest) -> Placement:
        """The port contract: a proposal venue's placement is pending until a
        human acknowledges; nothing is placed programmatically."""
        return Placement("proposal", request.spec_hash[:12], "pending", None,
                         "awaiting a human's acknowledgement; the venue places nothing")

    def acknowledge(self, ack: Acknowledgement) -> Decision:
        """Records the fill against the pending decision and returns that
        decision unchanged — an acknowledgement is never a veto (M9.8)."""
        d = self.pending.pop(ack.card_id, None)
        if d is None:
            raise KeyError(f"no pending card {ack.card_id}")
        return d
