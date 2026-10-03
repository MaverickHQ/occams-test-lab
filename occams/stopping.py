"""A programme stops in one of three ways, and each is a Register record
(M12.8). Its falsifier fires: ``LabClosed``, appended by the loop
(ADR-0033). Its alpha is exhausted: no runnable axis can afford the
smallest question the gates would let register. The author stops it, with
the reason. The last two are ``ProgrammeStopped``, the author's act::

    python -m occams programme stop --register R --config C --kind alpha|author [--reason "..."] --by NAME [--plateau-cells 4] [--yes]

Without ``--yes`` the command shows where the three conditions stand and
appends nothing. An alpha stop the ledger contradicts is refused with the
arithmetic; an author's stop without a reason is refused; a second stop is
refused. After any stopping record nothing prepares, registers, surveys or
measures in that Register, and the conclusion is written from it by
``python -m occams conclude`` — after, and not before.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path

from occams.register import ProgrammeStopped, Register

STOPPING_TYPES = ("LabClosed", "ProgrammeStopped")
KINDS = ("alpha", "author")
PLATEAU_CELLS = 4   # the smallest sweep a plateau can be shown on, as `question` defaults it


class StopRefused(RuntimeError):
    """A stop the Register or the ledger's arithmetic does not support."""


def stopping_record(register: Register) -> dict | None:
    """The record that stopped this programme, or None. Read from the
    Register every time, never remembered."""
    stops = [r for r in register.records() if r["type"] in STOPPING_TYPES]
    return stops[-1] if stops else None


def describe(rec: dict) -> str:
    if rec["type"] == "LabClosed":
        return (f"the lab's falsifier fired on {rec['falsifier_count']} {rec['outcome']} mechanism verdicts "
                f"({', '.join(rec['verdicts'])}) (ADR-0033)")
    if rec["kind"] == "alpha_exhausted":
        return f"its alpha is exhausted — no runnable axis can afford the smallest registrable question — recorded by {rec['by']}"
    return f"the author ({rec['by']}) stopped it: {str(rec['reason']).rstrip('.')}"


@dataclass(frozen=True)
class AxisRoom:
    axis: str
    remaining: float
    rate: float
    smallest_charge: float     # rate × plateau cells: the least a mechanism question on this axis could cost

    @property
    def affordable(self) -> bool:
        return self.remaining >= self.smallest_charge - 1e-12


@dataclass(frozen=True)
class Conditions:
    """Where the three stopping conditions stand, read from the config and the Register."""

    falsifier_standing: int
    falsifier_count: int
    falsifier_outcome: str
    fired: bool
    verdicts: tuple[tuple[str, str], ...]
    room: tuple[AxisRoom, ...]     # runnable axes only
    stopped: dict | None
    plateau_cells: int

    @property
    def alpha_exhausted(self) -> bool:
        return not any(r.affordable for r in self.room)

    def lines(self) -> list[str]:
        out = [f"falsifier: {self.falsifier_standing} of {self.falsifier_count} {self.falsifier_outcome} mechanism verdicts"
               + (" — fired" if self.fired else "")]
        for r in self.room:
            out.append(f"alpha on {r.axis}: {r.remaining:.4f} remaining against a smallest charge of {r.smallest_charge:.4f} "
                       f"({r.rate:.4f} × {self.plateau_cells} cells) — {'affordable' if r.affordable else 'exhausted'}")
        if not self.room:
            out.append("alpha: no runnable axis")
        out.append("alpha: exhausted on every runnable axis" if self.alpha_exhausted else "alpha: not exhausted")
        out.append(f"stopped: {describe(self.stopped)}" if self.stopped else "author's stop: none recorded")
        return out


def conditions(cfg, register: Register, *, plateau_cells: int = PLATEAU_CELLS) -> Conditions:
    from occams import falsifier
    from occams.hypothesis import Tier
    from occams.ledger.alpha_budget import AlphaBudget
    from occams.whatif import config_sha

    st = falsifier.standing(cfg, register)
    budget = AlphaBudget(cfg, register, config_sha=config_sha(cfg))
    room = []
    for ax, a in cfg.alpha.axes.items():
        if not a.runnable:
            continue
        rate = budget.rate(ax, Tier.MECHANISM)
        room.append(AxisRoom(ax.value, budget.remaining(ax), rate, rate * plateau_cells))
    standing = sum(1 for _, o in st.resolved if o == cfg.lab.falsifier_outcome)
    return Conditions(standing, cfg.lab.falsifier_count, cfg.lab.falsifier_outcome, st.fired, st.resolved, tuple(room),
                      stopping_record(register), plateau_cells)


def check(cfg, register: Register, *, kind: str, by: str, reason: str = "",
          plateau_cells: int = PLATEAU_CELLS) -> tuple[Conditions, str]:
    """What ``stop`` would record, or ``StopRefused`` with why. Appends nothing."""
    if kind not in KINDS:
        raise StopRefused(f"kind is one of {', '.join(KINDS)}, not {kind!r}")
    c = conditions(cfg, register, plateau_cells=plateau_cells)
    if c.stopped:
        raise StopRefused(f"already stopped — {describe(c.stopped)}; a programme stops once")
    if c.fired:
        raise StopRefused("the falsifier has fired and its record is the loop's to append (ADR-0033); run the loop, do not stop by hand")
    if not by.strip():
        raise StopRefused("a stop names who recorded it (--by)")
    if kind == "alpha":
        if not c.alpha_exhausted:
            room = "; ".join(f"{r.axis} has {r.remaining:.4f} against a smallest charge of {r.smallest_charge:.4f}"
                             for r in c.room if r.affordable)
            raise StopRefused(f"alpha is not exhausted: {room} — a question can still be registered there; "
                              f"spend it, or stop as the author with --kind author --reason")
        reason = reason.strip() or f"no runnable axis can afford the smallest registrable question (rate × {plateau_cells} cells)"
    elif not reason.strip():
        raise StopRefused("an author's stop names its reason (--reason)")
    return c, reason.strip()


def stop(cfg, register: Register, *, kind: str, by: str, reason: str = "",
         plateau_cells: int = PLATEAU_CELLS) -> ProgrammeStopped:
    """Append ``ProgrammeStopped`` after ``check`` passes."""
    from occams.whatif import config_sha

    c, why = check(cfg, register, kind=kind, by=by, reason=reason, plateau_cells=plateau_cells)
    records = register.records()
    rec = ProgrammeStopped("alpha_exhausted" if kind == "alpha" else "author", by.strip(), why,
                           {r.axis: round(r.remaining, 12) for r in c.room},
                           {r.axis: round(r.smallest_charge, 12) for r in c.room},
                           tuple(h for h, _ in c.verdicts),
                           sum(1 for r in records if r["type"] == "SurveyRecorded"),
                           sum(1 for r in records if r["type"] == "HypothesisRegistered"),
                           config_sha(cfg))
    register.append(rec)
    return rec


def main(argv: list[str] | None = None) -> int:
    from occams.config import ConfigRefused, load

    argv = sys.argv[1:] if argv is None else argv
    p = argparse.ArgumentParser(prog="python -m occams programme stop",
                                description="record that a programme stopped: its alpha is exhausted, or the author stops it (M12.8)")
    p.add_argument("--register", required=True)
    p.add_argument("--config", required=True)
    p.add_argument("--kind", required=True, choices=KINDS, help="alpha: exhausted, verified against the ledger; author: with --reason")
    p.add_argument("--reason", default="")
    p.add_argument("--by", required=True)
    p.add_argument("--plateau-cells", type=int, default=PLATEAU_CELLS, help="the smallest sweep a plateau can be shown on")
    p.add_argument("--yes", action="store_true", help="the human confirmation; without it nothing is appended")
    a = p.parse_args(argv)
    try:
        cfg = load(a.config)
    except ConfigRefused as e:
        print("REFUSED: the configuration does not load.")
        for r in e.reasons:
            print(f"  - {r}")
        return 2
    reg = Register(Path(a.register))
    c = conditions(cfg, reg, plateau_cells=a.plateau_cells)
    print(f"where the three stopping conditions stand in {a.register}:")
    for line in c.lines():
        print(f"  {line}")
    try:
        _, why = check(cfg, reg, kind=a.kind, by=a.by, reason=a.reason, plateau_cells=a.plateau_cells)
    except StopRefused as e:
        print(f"REFUSED: {e}")
        return 1
    if not a.yes:
        print(f"would append ProgrammeStopped ({'alpha exhausted' if a.kind == 'alpha' else 'author'}, by {a.by}): {why}. "
              f"Nothing appended without --yes.")
        return 0
    stop(cfg, reg, kind=a.kind, by=a.by, reason=a.reason, plateau_cells=a.plateau_cells)
    seq = reg.chain()[-1]["seq"]
    print(f"ProgrammeStopped appended (#{seq}): {describe(reg.records()[-1])}. Nothing prepares, registers, surveys or measures "
          f"after it; the conclusion is written from the Register: python -m occams conclude --register {a.register} --out PATH")
    return 0


if __name__ == "__main__":
    sys.exit(main())
