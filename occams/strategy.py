"""The Strategy aggregate — the deployable specification, the apparatus that
measures a Hypothesis (ADR-0001). It costs money, not alpha.

``SPECIFIED -> COMPILED -> MEASURED -> FORWARD -> APPROVED -> LIVE -> RETIRED``
with ``LIVE <-> HALTED`` (F0). The legal set is a frozen literal below, and
a test enumerates it — a transition not in the set raises before any guard
runs; a transition in the set runs its guard module, whose refusal is
recorded and raised.

At M2 the identity is a mapping; the StrategySpec that produces it arrives
at M3. The hash is the identity of what hashed, never its context (D4).
"""

from __future__ import annotations

import enum
import hashlib
import json
from dataclasses import dataclass, replace
from types import SimpleNamespace
from typing import Any
from collections.abc import Mapping

from occams.guards import Refused, refuse_or_pass


class StrategyState(enum.Enum):
    SPECIFIED = "SPECIFIED"
    COMPILED = "COMPILED"
    MEASURED = "MEASURED"
    FORWARD = "FORWARD"
    APPROVED = "APPROVED"
    LIVE = "LIVE"
    HALTED = "HALTED"
    RETIRED = "RETIRED"


S = StrategyState
LEGAL: frozenset[tuple[StrategyState, StrategyState]] = frozenset({
    (S.SPECIFIED, S.COMPILED),
    (S.COMPILED, S.MEASURED),
    (S.MEASURED, S.FORWARD),
    (S.FORWARD, S.APPROVED),
    (S.APPROVED, S.LIVE),
    (S.LIVE, S.HALTED),
    (S.HALTED, S.LIVE),
    (S.MEASURED, S.RETIRED),
    (S.FORWARD, S.RETIRED),
    (S.APPROVED, S.RETIRED),
    (S.LIVE, S.RETIRED),
    (S.HALTED, S.RETIRED),
})


class IllegalTransition(ValueError):
    pass


def spec_hash(identity: Mapping[str, Any]) -> str:
    """Identity, not context (D4): the mapping's canonical JSON, hashed."""
    return hashlib.sha256(json.dumps(dict(identity), sort_keys=True, separators=(",", ":"),
                                     default=str).encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Strategy:
    identity: tuple[tuple[str, Any], ...]
    hypothesis_id: str | None = None
    state: StrategyState = StrategyState.SPECIFIED
    measurement: Any = None
    spec: Any = None  # a StrategySpec once M3 supplies one; its identity() is the mapping above

    @classmethod
    def specify(cls, identity: Mapping[str, Any], *, hypothesis_id: str | None = None) -> Strategy:
        return cls(tuple(sorted((k, v) for k, v in identity.items())), hypothesis_id)

    @classmethod
    def from_spec(cls, spec, *, hypothesis_id: str | None = None) -> Strategy:
        ident = spec.identity()
        return cls(tuple(sorted((k, json.dumps(v, sort_keys=True)) for k, v in ident.items())),
                   hypothesis_id, spec=spec)

    @property
    def spec_hash(self) -> str:
        if self.spec is not None:
            return self.spec.hash
        return spec_hash(dict(self.identity))


def _guard_for(a: StrategyState, b: StrategyState):
    from occams.guards import approve, compile, forward, halt, live, measured, resume, retire

    if b is S.RETIRED:
        return retire
    return {
        (S.SPECIFIED, S.COMPILED): compile,
        (S.COMPILED, S.MEASURED): measured,
        (S.MEASURED, S.FORWARD): forward,
        (S.FORWARD, S.APPROVED): approve,
        (S.APPROVED, S.LIVE): live,
        (S.LIVE, S.HALTED): halt,
        (S.HALTED, S.LIVE): resume,
    }[(a, b)]


def transition(s: Strategy, to: StrategyState, *, register, hypothesis=None, **ctx) -> Strategy:
    """Move ``s`` to ``to``. Illegal pairs raise ``IllegalTransition`` before
    any guard runs. A guard refusal is appended to the Register and raised
    as ``Refused``; the Strategy is unchanged."""
    if (s.state, to) not in LEGAL:
        raise IllegalTransition(f"{s.state.value} -> {to.value} is not a legal transition")
    context = SimpleNamespace(hypothesis=hypothesis, **ctx)
    guard = _guard_for(s.state, to)
    if (s.state, to) == (S.MEASURED, S.FORWARD):
        if hypothesis is None:
            raise Refused((_no_hypothesis(),))
        result = guard.check(s.measurement, hypothesis)
    else:
        result = guard.check(s, context)
    refuse_or_pass(result, register, spec_hash=s.spec_hash, hypothesis_id=s.hypothesis_id)
    changes: dict[str, Any] = {"state": to}
    if to is S.MEASURED:
        changes["measurement"] = context.measurement
    out = replace(s, **changes)
    register.append(register.StrategyTransitioned(s.spec_hash, s.state.value, to.value, s.hypothesis_id))
    return out


def _no_hypothesis():
    from occams.guards import Refusal

    return Refusal("MEASURED->FORWARD", "no Hypothesis supplied: the five checks are evaluated against a declared floor, plan and gates", {})
