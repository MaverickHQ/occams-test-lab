# How this lab prevents p-hacking

Every guard below exists because of a way a backtest lies. Each is mapped
to the failure it stops, to where it lives in the code, and to the record
that showed the failure or the decision that closed it — a record number
in one of the three Registers (`register.jsonl` for programme 1,
`programme-2.jsonl`, `programme-3.jsonl`) or an ADR under `docs/adr/`.
Nothing here recommends a number; the floor, the alpha split and the
falsifier count are the author's and have no default anywhere (R9, R4).

| The failure | The guard | Where it lives | The record |
|---|---|---|---|
| Testing a hundred ideas and reporting the one that worked | An alpha budget per axis, priced per cell of the sweep, charged before measurement; exhaustion is terminal | `occams/ledger/`, `AlphaSpent` before `HypothesisRegistered` | P3 #10–#11; P2 #36 (0.05 left on each axis against a smallest charge of 0.04 — nothing more affordable) |
| Deciding what "worked" after seeing the result | The floor and the sweep declared at registration; the loop never registers; the `--yes` is a human's | `HypothesisRegistered.floor_ev_net_r`, ADR-0035 | P1 #24 (floor 0.15 R, 50 a year); P1 #27 (Q-005 refused by that floor at +0.051) |
| Peeking at the test set | Three partitions cut from a frozen calendar: definition (may be read), measurement (read once, by a registered question), reserve (sealed) | `occams/data/partitions.py`, ADR-0038, ADR-0006, `ObservationsConsumed` | P1 #22, P2 #1–#7, P3 #4–#7 (the calendars); P2 #14 (Q2-001 consumed 98 names on the measurement partition, once) |
| A winner that random entry matches | beats-null: the same geometry under random entry with a coin-flip side, at the corrected alpha | `occams/guards/beats_null.py` | P1 #15 (Q-004), P1 #9 (Q-003) |
| A winner that is one lucky cell | plateau: the neighbourhood must hold at the declared slack; a sweep too small to show one is refused at registration | `occams/guards/plateau.py`, M8.4 | P1 #14 (Q-004: neighbourhood too small) |
| A winner one name carries | leave-one-out: the pooled effect must survive every omission; fewer than three groups is a refusal | `occams/guards/leave_one_out.py`, ADR-0012 | P1 #17 (Q-004), P1 #28 (Q-005, carried by IWM) |
| A winner too small to trade | the floor, absolute EV in net R and trades per year, declared before the run | `occams/guards/clears_floor.py` | P1 #16, P1 #27, P2 #29 (Q2-002 at +0.109 against 0.15) |
| A winner the market would have paid anyway | beats-always-long: always-long at the same geometry and gate, at the corrected alpha — the fifth check | `occams/guards/beats_always_long.py`, ADR-0043 | P2 #24 (Q2-001: +0.213 measured, always-long +0.214, margin −0.001 — the record that created the check); P2 #33 (Q2-002 judged under it) |
| Ranking cells by one statistic and judging by another | The sweep's surface is the margin over always-long for the winner, the plateau and leave-one-out; the floor stays absolute | `Measurement.surface`, ADR-0045 | P2 #33 (`surface: margin`); P2 #35 (definition margin +0.201, measured +0.075) |
| A promise of power the guard will not honour | required N against available N at registration, effective after measured ρ; at measurement the winning cell's own trades; the promise is the sweep's thinnest cell's, not the template's signals | `occams/guards/measure.py`, M8.2, M7.7, `bound_by_thinnest_cell`, `precommit(sweep=)` | P3 #12 (Q3-001: 863 held, 1,068 required); the correction of 2026-09-20 and M13.9 |
| Correlated trades counted as independent | ρ measured on the definition partition's signals; N becomes effective N | `occams/proposers/clustering.py`, M7.7 | every `HypothesisRegistered` carries `available_n` after ρ; P3 #11 (2,327 effective from 4,469) |
| Stopping when the story is good | The falsifier: a count of null mechanism verdicts, declared before the first question, at which the lab closes; a programme otherwise stops only by the author's record | ADR-0033, `LabClosed`; M12.8, `ProgrammeStopped` | P1 #33 (the third null closed the first lab); P2 #36, P3 #13 (the author's stops, with the ledger's arithmetic beside them) |
| Screening thousands of cells and calling one a finding | A survey runs on the definition partition only, at zero alpha, and is never a verdict; every cell screened is stamped on every question registered from it; the shrinkage from screening is a record | `occams/survey/`, N6, `Shrinkage` | P2 #9 (38,976 cells); P2 #13 (`screened_cells: 38976`); P2 #24, #35 (definition against measured) |
| A result that cannot be reproduced | Every verdict stamps its seed, spec hash, engine and engine code hash; the archive is content-addressed; private reproduction recreates a verdict or fails loudly, public reproduction runs on fixtures and refuses an exact-historical claim | `occams/reproduce.py`, M11.5, M11.6, M14.3 | Q-005 reproduced exactly both ways (2026-09-18); `engine_sha` on every `HypothesisResolved` |
| A record edited after the fact | Hash-chained, append-only stores; a tampered file cannot be extended; a correction supersedes and names what it supersedes (R4.9) | `occams/register/store.py`, `TamperedHistory` | P1 #11 (Q-004 supersedes Q-003, with its distinction) |
| Guards that drift | A coin flip through the whole pipeline must be refused and a planted effect at the floor accepted, on both engines, on every build and in CI | `make null`, `make signal`, `occams/controls.py`, S3, S10 | every `check` run; the console recomputes both on every build |
| Fills the venue would not have given | Obtainability auditors on every fill; an unobtainable entry is a missed trade counted by name, never silently dropped | ADR-0040–0042, `Trades.missed` | P2 #23 (Q2-001: one missed entry, named) |
| A universe that only holds survivors | The source serves no delisted history and a symbol is not an identity; survivorship is a named bias on every universe record | M12.1b, M12.1c, `UniverseDeclared.bias` | P2 #6, #11 (the S&P 100 universe with its bias in the same words) |
| A default that is a recommendation | Capital, drawdown, risk, the alpha split and the falsifier count are required configuration with no default; the schema prints keys and never values; no page carries money | `occams/config.py` and the test that keeps it so, S7, `tools/prepublish.py` | `python -m occams --schema`; `make prepublish` on every page |

## What the table does not claim

A lab that cannot p-hack can still find nothing, and this one found
nothing: four null verdicts, one supported whose entry added nothing, one
refusal at measurement (`docs/LAB-CONCLUSION.md`). The guards make a
finding believable; they do not make one. What they cost is written
beside them — 0.55 of 1.20 alpha across three programmes, and a survey
that screened 77,952 cells to register three questions.

## Reading the evidence yourself

```bash
make console            # every record, rendered; the controls recomputed inside the build
make programme          # what was searched, what it cost, what was found, per programme
python -m occams refusals --register register/programme-2.jsonl    # why each thing died, from the Register alone
```

Every number in this document is in a Register; `docs/console.html` shows
the chain, and a tampered Register is a failure, not a report.
