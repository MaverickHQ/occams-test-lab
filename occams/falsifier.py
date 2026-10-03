"""The lab's own falsifier, evaluated mechanically against the Register
(ADR-0033, R3.1, D27). Declared in ``[lab]`` before the first verdict:
when the first ``falsifier_count`` resolved **mechanism** verdicts are all
the declared outcome, the lab closes. Superseded hypotheses count; nothing
is judged in the moment."""

from __future__ import annotations

from dataclasses import dataclass

from occams.config import Config
from occams.register import LabClosed, Register


@dataclass(frozen=True)
class Standing:
    resolved: tuple[tuple[str, str], ...]  # (hypothesis_id, outcome), mechanism tier, in order
    fired: bool
    closed_already: bool


def mechanism_verdicts(register: Register) -> tuple[tuple[str, str], ...]:
    tiers = {r["hypothesis_id"]: r["tier"] for r in register.records() if r["type"] == "HypothesisRegistered"}
    caps = {r["hypothesis_id"] for r in register.records() if r["type"] == "HypothesisRegistered" and r.get("capability")}
    out = []
    for r in register.records():
        if r["type"] == "HypothesisResolved" and tiers.get(r["hypothesis_id"]) == "mechanism" \
                and r["hypothesis_id"] not in caps:
            out.append((r["hypothesis_id"], r["outcome"]))
    return tuple(out)


def standing(cfg: Config, register: Register) -> Standing:
    verdicts = mechanism_verdicts(register)
    n = cfg.lab.falsifier_count
    first = verdicts[:n]
    fired = len(first) == n and all(o == cfg.lab.falsifier_outcome for _, o in first)
    closed = any(r["type"] == "LabClosed" for r in register.records())
    return Standing(verdicts, fired, closed)


def evaluate(cfg: Config, register: Register) -> Standing:
    """Append ``LabClosed`` the first time the rule holds. Idempotent."""
    st = standing(cfg, register)
    if st.fired and not st.closed_already:
        register.append(LabClosed(cfg.lab.falsifier_count, cfg.lab.falsifier_outcome,
                                  tuple(h for h, _ in st.resolved[:cfg.lab.falsifier_count])))
        return Standing(st.resolved, True, True)
    return st
