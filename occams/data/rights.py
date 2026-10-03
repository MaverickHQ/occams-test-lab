"""The data-rights matrix, machine-readable and enforced (F18.7, M4.9).

Every source records five answers. Ingestion refuses a source with no
record and any use the record does not ALLOW — ``UNANSWERED`` is a
refusal, not a maybe, because a right nobody has confirmed is a right
nobody has. The Tiingo entry is M0.3's finding of 2026-09-10; the
synthetic source is ours and allows everything.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping


class Use(enum.Enum):
    PRIVATE_RETENTION = "private_retention"
    INTERNAL_REPRODUCTION = "internal_reproduction"
    RAW_REDISTRIBUTION = "raw_redistribution"
    DERIVED_ARTIFACTS = "derived_artifacts"
    SYNTHETIC_PUBLICATION = "synthetic_publication"


class Answer(enum.Enum):
    ALLOWED = "allowed"
    FORBIDDEN = "forbidden"
    UNANSWERED = "unanswered"


class RightsRefused(PermissionError):
    pass


@dataclass(frozen=True)
class Rights:
    source_id: str
    recorded_on: str
    provenance: str
    uses: Mapping[Use, Answer]
    notes: str = ""   # dated observations about the source that its terms do not state (M12.1b)

    def __post_init__(self):
        missing = set(Use) - set(self.uses)
        if missing:
            raise ValueError(f"rights for {self.source_id} leave uses unrecorded: {sorted(u.value for u in missing)}")
        object.__setattr__(self, "uses", MappingProxyType(dict(self.uses)))

    def permits(self, use: Use) -> bool:
        return self.uses[use] is Answer.ALLOWED

    def time_bounded(self) -> bool:
        """Norgate-style: retention ends with the subscription (M0.6 finding)."""
        return "expiry" in self.provenance.lower()


TIINGO_STARTER = Rights(
    source_id="tiingo-starter",
    recorded_on="2026-09-10",
    provenance="docs/M0-ANSWERS.md §M0.3 — tiingo.com/about/pricing 'Internal Use Only'; "
               "redistribution priced separately; derived-artefact publication not addressed in the terms",
    uses={Use.PRIVATE_RETENTION: Answer.ALLOWED,
          Use.INTERNAL_REPRODUCTION: Answer.ALLOWED,
          Use.RAW_REDISTRIBUTION: Answer.FORBIDDEN,
          Use.DERIVED_ARTIFACTS: Answer.UNANSWERED,   # refuse until a written answer is recorded (M4.9)
          Use.SYNTHETIC_PUBLICATION: Answer.ALLOWED},
    notes="delisted coverage probed 2026-09-12 (M12.1b): FRC not found (HTTP 404); BBBY known, no rows; "
          "SHLD served the symbol's 2023 holder, not the 2005-2018 company. Delisted history is not served and a "
          "reassigned symbol serves its new holder silently: survivorship stays a named bias on every single-name "
          "universe; a delisted-capable source must be keyed by instrument identity, not symbol (docs/M0-ANSWERS.md §M0.3). "
          "Close-only prints observed 2026-09-12 (M12.3): some early bars carry volume but open = high = low = close — "
          "C for every bar of 1996, 319 such bars across the S&P 100's definition partition; the fill auditor refuses them")

SYNTHETIC = Rights(
    source_id="synthetic",
    recorded_on="2026-09-10",
    provenance="generated here from a seed; no licence applies",
    uses={u: Answer.ALLOWED for u in Use})

REGISTRY: dict[str, Rights] = {r.source_id: r for r in (TIINGO_STARTER, SYNTHETIC)}


def require(source_id: str, use: Use, registry: Mapping[str, Rights] = REGISTRY) -> Rights:
    r = registry.get(source_id)
    if r is None:
        raise RightsRefused(f"source {source_id!r} has no recorded rights matrix; ingestion refuses it (F18.7)")
    if not r.permits(use):
        raise RightsRefused(f"{source_id} does not permit {use.value}: recorded answer is {r.uses[use].value}"
                            + (" — ask the vendor in writing before relying on it" if r.uses[use] is Answer.UNANSWERED else ""))
    return r
