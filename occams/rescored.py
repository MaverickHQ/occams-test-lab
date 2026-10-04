"""Reading a re-score (M16.19; ADR-0047): the diagnostics store's records as sentences — for the report, the console
and the programme page, which show each one **beside the verdict it annotates and never in its place**::

    python -m occams rescore report --out docs/RESCORE-2026-10.md      # written from register/diagnostics.jsonl alone

Nothing here measures, and nothing here is a verdict. It reads one store.
"""

from __future__ import annotations

import sys
from pathlib import Path

from occams.register import Diagnostics

ROOT = Path(__file__).resolve().parent.parent
STORE = ROOT / "register" / "diagnostics.jsonl"
REPORT = "docs/RESCORE-2026-10.md"


def load(store: Path = STORE) -> tuple[list[dict], str]:
    """(the records, the store's head) — the chain verified first; an absent store is no records."""
    if not Path(store).exists():
        return [], "genesis"
    chain = Diagnostics(Path(store)).chain()
    return [line["payload"] for line in chain], (chain[-1]["sha"] if chain else "genesis")


def beside(store: Path, register_name: str) -> dict[str, dict]:
    """hypothesis id -> its latest ``Rescored``, for the Register of that file name."""
    return {r["hypothesis_id"]: r for r in load(store)[0] if r["register"] == register_name}


LABEL = {"plateau": "plateau", "beats_null": "beats-null", "clears_floor": "floor", "leave_one_out": "leave-one-out",
         "beats_always_long": "beats-always-long"}


def _f(x, places: int = 3, sign: bool = True) -> str:
    return "—" if x is None else f"{float(x):{'+' if sign else ''}.{places}f}"


def _p(x) -> str:
    if x is None:
        return "—"
    return f"{x:.4f}" if x >= 0.00005 else f"{x:.1e}"


def _heads(reasons) -> str:
    return ", ".join(str(r).split(":")[0] for r in reasons) or "none"


def revived(records) -> list[tuple[str, str]]:
    """Every (question, check) that refused as recorded and passes under the corrected rules. ADR-0047 §5 says a null is
    never revived; this is read off the store, so the report says what happened and not what was meant to."""
    out = []
    for p in records:
        passing = {LABEL[c["check"]] for c in p.get("checks") or [] if c["passed"]}
        out += [(p["hypothesis_id"], h) for h in (str(r).split(":")[0] for r in p["recorded"].get("refusals") or []) if h in passing]
    return out


def _second_look(records) -> str:
    back = revived(records)
    found = ("No check that refused a question as recorded passes it here, and no outcome reads better than its record."
             if not back else "**" + "; ".join(f"{q}'s {h}" for q, h in back) + " refused as recorded and would pass here**: read those "
             "lines as the corrected test's answer, never as a null revived.")
    return ("- **Not a second look that spends nothing.** A re-score reads the measurement partition again. ADR-0047 §5 admits it "
            f"on one condition, that a null is never revived on a guard set known to be too loose. {found}")


def _check_line(c: dict) -> str:
    e, name = c["evidence"], c["check"]
    said = "passes" if c["passed"] else "refuses"
    if name == "plateau":
        if "gap" not in e:
            return f"**plateau** {said}: a neighbourhood of {e.get('neighbourhood')} against the {e.get('plateau_cells')} declared."
        se = f", {_f(e['gap_se'], 2, False)} of its standard errors (recorded, not judged)" if e.get("gap_se") is not None else ""
        return (f"**plateau** {said}: the winner is {_f(e['gap'])} R over its neighbours' median against a slack of "
                f"{_f(e['plateau_slack'], 2, False)}{se}.")
    if name == "beats_null":
        return (f"**beats-null** {said}: p {_p(e.get('p_null'))} by the bootstrap and {_p(e.get('p_cluster'))} by the clustered standard "
                f"error, against {_p(e.get('alpha_corrected'))}; a coin's side makes {_f(e.get('reference'))} R.")
    if name == "clears_floor":
        return (f"**floor** {said}: the lower confidence bound is {_f(e.get('lcb_ev_net_r'))} R against a floor of "
                f"{_f(e.get('floor_ev_net_r'), 2)}; {_f(e.get('trades_per_year'), 1, False)} trades a year against "
                f"{_f(e.get('floor_min_trades_per_year'), 0, False)}.")
    if name == "leave_one_out":
        if "weakest_group" in e:
            return (f"**leave-one-out** {said}: without {e['weakest_group']} the score is {_f(e.get('weakest_score_without'))} against "
                    f"{_f(e.get('pooled_score'))} pooled.")
        return f"**leave-one-out** {said}: {str(e.get('reason', '')).split(': ', 1)[-1]}."
    return (f"**beats-always-long** {said}: the passive alternative makes {_f(e.get('reference'))} R; the margin of "
            f"{_f((e.get('selection') or 0) + (e.get('execution') or 0))} is {_f(e.get('selection'))} selection and "
            f"{_f(e.get('execution'))} execution; p {_p(e.get('p_baseline'))} and {_p(e.get('p_cluster'))} against {_p(e.get('alpha_corrected'))}.")


def _needs(a: dict) -> str:
    need = (a.get("evidence") or {}).get("required_n_at_winner_sd")
    return f", and its own dispersion requires {need:,}" if not a["passed"] and need else ""


def one_line(p: dict) -> str:
    """The reading in a sentence, for a table cell."""
    if not p["reproduced"]:
        return "not re-scored: " + ("its refusal stamps no engine" if p["recorded"]["outcome"] == "refused at measurement" else "not recreated")
    refused = ", ".join(LABEL[c] for c in p["refused_by"]) or "nothing"
    if p["reading"] == "would be refused at measurement":
        return f"would be refused at measurement, underpowered at its own dispersion; of the five checks, refused by {refused}"
    return f"{p['reading']}; refused by {refused}"


ORDER = ("register.jsonl", "programme-2.jsonl", "programme-3.jsonl")


def in_order(records: list[dict]) -> list[dict]:
    """By programme, then by the place of the record each annotates: the order the lab asked them in."""
    return sorted(records, key=lambda p: (ORDER.index(p["register"]) if p["register"] in ORDER else len(ORDER), p["annotates_seq"]))


def report(records: list[dict], *, head: str, count: int) -> str:
    records = in_order(records)
    out = ["# The re-score of October 2026", "",
           "**This document has no standing.** It is written from `register/diagnostics.jsonl` and nothing else, and nothing in it is a "
           "verdict. The six questions of this lab were resolved, or refused, under the rules in force when they ran; those records are "
           "sealed and none of them is changed here (ADR-0047). An external review then found the rules looser than they claimed, and "
           "they were corrected, forward only. This is what the corrected rules would have said, beside the record.", "",
           f"The store holds {count} records and its head is `{head[:12]}`. Each record names the rule set it was judged under in full, "
           "the commit and the content hash of the code that judged it, and every number of every check, passing or failing.", "",
           "## How each question was treated", "",
           "1. **Recreated first.** The question was measured again in the code of the commit its record stamps, from that commit's "
           "snapshot (`SOURCES.toml`), and compared with the record: the winner, its EV, its count, the checks that refused it. A "
           "question not recreated exactly is not re-scored.",
           "2. **Then judged again**, by the present code, on the same bars and the stamped seed.",
           "3. **Only on what it declared.** The floor's lower confidence bound needs no new number and is judged against the recorded "
           "floor. No question declared a slack in standard errors or an alternative to plan its power against: those are reported, "
           "not judged.", "",
           "## At a glance", "",
           "| Question | As recorded | Recreated from its source | Under the corrected rules |", "|---|---|---|---|"]
    for p in records:
        r = p["recorded"]
        refused = f"refused by {_heads(r['refusals'])}" if r.get("refusals") else "no check refused it"
        was = (f"{r['outcome']}, EV {_f(r.get('ev_net_r'))} R over {r.get('n'):,} trades; {refused}"
               if r["outcome"] != "refused at measurement" else f"refused at measurement: {r['evidence'].get('n'):,} trades against "
               f"{r['evidence'].get('required_n'):,} required")
        again = "exactly" if p["reproduced"] else "no"
        out.append(f"| `{p['hypothesis_id']}` | {was} | {again} | {one_line(p)} |")
    out += ["", "## Question by question", ""]
    for p in records:
        r = p["recorded"]
        out += [f"### {p['hypothesis_id']}", "",
                f"Annotates record #{p['annotates_seq']} of `{p['register']}` (`{p['annotates_sha'][:12]}`)."]
        if not p["reproduced"]:
            out += ["", f"**Not recreated, so not re-scored.** {p['reproduction']['reason'][0].upper()}{p['reproduction']['reason'][1:]}.", ""]
            continue
        w, a = p["winner"], p["at_measurement"]
        same = "the recorded winner" if w["is_the_recorded_winner"] else "**not** the recorded winner: the surface is the margin now (ADR-0045, ADR-0049)"
        out += ["", f"**Recreated exactly** at `{p['reproduction']['source'][:12]}`: EV {_f(p['reproduction']['measured']['ev_net_r'], 4)} R over "
                f"{p['reproduction']['measured']['n']:,} trades, refused by {', '.join(p['reproduction']['measured']['refused_by']) or 'nothing'}.", "",
                f"**Under {', '.join(p['rules'])}**, seed {p['seed']}, {p['null_draws']:,} draws, code `{p['engine_sha'][:12]}` "
                f"(content `{p['engine_code_sha']}`): **{p['reading']}**.", "",
                f"- The winner is cell {w['cell']} — {same} — with {w['n']:,} trades, EV {_f(w['ev_net_r'])} R, its passive alternative "
                f"{_f(w['baseline_ev_net_r'])} R, margin {_f(w['margin_net_r'])} R.",
                f"- At measurement: {'passes' if a['passed'] else 'refused — ' + a['reason']}. Its own dispersion is "
                f"{_f(a.get('sd'), 2, False)} R against a plan of {_f(a.get('plan_sigma_r'), 2, False)}; its {a.get('n'):,} trades are worth "
                f"{_f(a.get('n_eff'), 0, False)} independent ones{_needs(a)}."]
        out += [f"- {_check_line(c)}" for c in p["checks"]]
        out += [""]
    out += ["## What this is not", "",
            "- **Not a verdict.** No outcome in any Register changed. The falsifier's count and every alpha balance are what they were.",
            _second_look(records),
            "- **Not complete.** It does not correct for the survey's selection of its candidates, for questions that share a "
            "partition, or for today's members measured on earlier history. Those are the successor lab's (README, *Known limitations*).", ""]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    import argparse

    ap = argparse.ArgumentParser(prog="python -m occams rescore report")
    ap.add_argument("--diagnostics", type=Path, default=STORE)
    ap.add_argument("--out", type=Path, default=ROOT / REPORT)
    a = ap.parse_args(sys.argv[1:] if argv is None else argv)
    records, head = load(a.diagnostics)
    if not records:
        print(f"REFUSED: {a.diagnostics} holds no record; a report is written from the diagnostics and from nothing else")
        return 2
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(report(records, head=head, count=len(records)), encoding="utf-8")
    print(f"{a.out}: written from {len(records)} record(s), head {head[:12]}; it has no standing, and says so")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
