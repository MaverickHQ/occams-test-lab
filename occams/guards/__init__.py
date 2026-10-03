"""One module per transition, each returning ``None`` or ``Refusal``.

A refusal is a recorded decision, never discarded (R3): ``refuse_or_pass``
appends it to the Register and raises ``Refused``. Nothing here returns a
boolean, because a boolean can be ignored.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Refusal:
    transition: str
    reason: str
    evidence: dict = field(default_factory=dict)


class Refused(Exception):
    def __init__(self, refusals: tuple[Refusal, ...]):
        self.refusals = refusals
        super().__init__("; ".join(f"{r.transition}: {r.reason}" for r in refusals))


def refuse_or_pass(result, register, *, spec_hash: str | None, hypothesis_id: str | None) -> None:
    """``result`` is None, one Refusal, or a tuple of them. Any refusal is
    appended to the Register and then raised."""
    if result is None:
        return
    refusals = tuple(result) if isinstance(result, tuple) else (result,)
    if not refusals:
        return
    for r in refusals:
        register.append(register.RefusalRecorded(r.transition, r.reason, dict(r.evidence),
                                                 spec_hash, hypothesis_id))
    raise Refused(refusals)
