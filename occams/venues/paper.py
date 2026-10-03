"""The paper venue: simulated fills, for the port contract test and for
keeping CI offline (M10.8). Its fills evidence nothing about cost or
obtainability, which is why a forward window wired to it is refused
(ADR-0032, M9.4b)."""

from __future__ import annotations

from dataclasses import dataclass, field

from occams.venues import OrderRequest, Placement


@dataclass
class PaperVenue:
    kind: str = "paper"
    placed: list[OrderRequest] = field(default_factory=list)

    def place(self, request: OrderRequest) -> Placement:
        self.placed.append(request)
        price = request.level if request.level is not None else 0.0
        return Placement("paper", f"paper-{len(self.placed)}", "filled", price, "simulated fill: evidences nothing")
