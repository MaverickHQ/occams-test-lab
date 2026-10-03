"""The universe is a point-in-time rule, not a list (D8, ADR-0025, M4.10).
Membership is evaluated at a day from the full listed set, later-delisted
names included; names enter and leave as they did in life.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from occams.spec.spec import UniverseRule


@dataclass(frozen=True)
class Listing:
    name: str
    venue: str
    listed_day: int
    delisted_day: int | None = None  # the first day the name no longer trades

    def listed_on(self, day: int) -> bool:
        return self.listed_day <= day and (self.delisted_day is None or day < self.delisted_day)


KNOWN_TERMS = {"venue", "min_adv_shares", "min_listed_days", "world"}


def evaluate(rule: UniverseRule, listings: tuple[Listing, ...], *, as_of_day: int,
             adv: Mapping[str, float] | None = None) -> frozenset[str]:
    terms = dict(rule.terms)
    unknown = set(terms) - KNOWN_TERMS
    if unknown:
        raise ValueError(f"UniverseRule has terms no evaluator knows: {sorted(unknown)}")
    out = set()
    for lst in listings:
        if not lst.listed_on(as_of_day):
            continue
        if "venue" in terms and lst.venue != terms["venue"]:
            continue
        if "min_listed_days" in terms and as_of_day - lst.listed_day < terms["min_listed_days"]:
            continue
        if "min_adv_shares" in terms:
            if adv is None or lst.name not in adv:
                continue  # unknown liquidity is not membership
            if adv[lst.name] < terms["min_adv_shares"]:
                continue
        out.add(lst.name)
    return frozenset(out)
