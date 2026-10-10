# The lab's closing statement — what three programmes established

**Dated 2026-09-23. Adopted by the author on 2026-09-24**, as written, on the author's instruction ("Let's adopt this closing statement"). Written from the three
Registers — `register.jsonl` (34 records, head `c2706a09716b`),
`programme-2.jsonl` (37, head `23cf22aa6586`) and `programme-3.jsonl` (14,
head `e92fda14a7f1`) — beside `docs/programme.html` and the three adopted
conclusions. Every number here is a record's; the Register does not
choose, and this statement recommends nothing.

## 1. The scoreboard, three programmes

| | Programme 1 | Programme 2 | Programme 3 |
|---|---|---|---|
| ran | 2026-09-11 → 2026-09-12 | 2026-09-12 → 2026-09-20 | 2026-09-20 → 2026-09-22 |
| records | 34 | 37 | 14 |
| universes declared | one, the four index ETFs | four: 4, 11, 30 and 101 names | the same four, re-declared |
| survey | none — three Drafts | `grid-001`, 38,976 cells (#9, seed 20260912) | `grid-002`, 38,976 cells (#9, seed 20260920) |
| questions registered | `Q-003`, `Q-004`, `Q-005` | `Q2-001`, `Q2-002` | `Q3-001` |
| verdicts | three null | one supported, one null | none — refused at measurement (#12) |
| alpha spent | 0.10 | 0.30 | 0.15 |
| how it ended | `LabClosed` on the third null (#33, ADR-0033) | the author's stop (#36) | the author's stop (#13) |
| conclusion | adopted 2026-09-20 | adopted 2026-09-20 | adopted 2026-09-22 |

Across the three: 77,952 cells screened at zero alpha; six questions
registered by the author; five verdicts reached by the machine against a
floor declared before each run — four null, one supported; one question
refused at measurement before a verdict; 0.55 of the 1.20 alpha declared
across the axes spent, the three reserves of 0.10 never looked at
(ADR-0006); 120 names archived under a rights record each; every
partition cut from a frozen calendar (ADR-0038); every verdict at bounded
costs (M5.0 closed by decision); nothing traded, no order placed, no
account used (ADR-0044).

**The verdicts, each beside its origin and its measured numbers:**

| question | origin | EV net R | trades | outcome, and why |
|---|---|---|---|---|
| `Q-003` | Draft, index ETFs, regime axis | −0.047 | 1,391 | null: beats-null and the floor refused; too few groups for leave-one-out |
| `Q-004` | Draft, superseding `Q-003` on SPY, QQQ, DIA | −0.045 | 2,088 | null: every check refused |
| `Q-005` | Draft, reversal after a down-run (ADR-0037) | +0.051 | 893 | null: the floor and leave-one-out refused (carried by IWM) |
| `Q2-001` | survey cell, S&P 100, four-day down-run in the up regime | +0.213 | 6,946 | **supported** by four checks; margin over always-long −0.001 (Shrinkage #24) |
| `Q2-002` | survey cell, S&P 100, the same mechanism ungated | +0.109 | 12,732 | null on the floor alone, under five checks and the margin surface; margin +0.075 (#33) |
| `Q3-001` | survey cell, sector ETFs, pullback in trend in the up regime | — | 863 held | refused at `REGISTERED -> MEASURED`: 1,068 required (#12) |

## 2. What the Register establishes

- **Five mechanisms were put to the measurement partition against a
  declared floor and four were not there.** Three in the first programme
  (`Q-003`, `Q-004`, `Q-005`), one in the second (`Q2-002`): each refused
  by the floor, three of them by beats-null or leave-one-out as well. The
  falsifier fired on the third (ADR-0033) and closed the first lab.
- **One mechanism cleared the four checks the lab then had, and the
  record beside it says the entry added nothing.** `Q2-001`: EV +0.213 net
  R over 6,946 trades, 412.7 a year, beats-null, plateau, floor and
  leave-one-out passed (#22); always-long at the winner's geometry and
  gate on the same partition makes +0.214 (#24). The verdict stands as
  reached; the diagnostic beside it is why the lab now has a fifth check
  (ADR-0043) and judges the sweep on the margin (ADR-0045), binding from
  the next registration and never re-judging the one that showed the gap.
- **The same mechanism, chosen by margin, beat always-long and missed the
  floor.** `Q2-002`: +0.109 net R over 12,732 trades, four of five checks
  passed, the floor refused by 0.041 R, measured margin +0.075 against
  the screen's +0.201 (#33). One winner rule asked *is there money here?*
  and got yes for the wrong reason; the other asked *does the entry earn
  it?* and got yes, not enough.
- **A screen's statistic did not predict transfer, twice.** All twenty
  candidates of each survey passed the fifth check on the definition
  partition with a positive margin in every era; the one that was
  measured lost its whole margin, and the one registered in the third
  programme never reached the check.
- **Three Drafts, two grids, six questions, one refusal: the pipeline
  refused a dead world and accepted a planted edge before every one of
  them** (S3, S10), on both engines, and does so on every build of the
  console. No verdict was reached while a control was wrong.

## 3. What is not established

- **Anything about any mechanism beyond the six questions.** 77,946 of
  the 77,952 cells screened were never registered; a screen is not a
  verdict and a cell not registered says nothing.
- **Whether a margin the screen finds transfers** — the question
  ADR-0046 opened the third programme to ask. Its one question was refused
  at measurement; the apparatus to ask it stands ready and the numbers to
  afford it were not declared.
- **Anything at measured costs, in a forward window, or live.** Every
  verdict is at bounded costs; the one Strategy that reached `FORWARD`
  (`Q2-001`'s winner) stands there as a record, because the execution
  host is deferred outside this lab (ADR-0044); `APPROVED -> LIVE` was
  never taken.
- **Anything about the reserves, the fundamental axis, crypto, intraday
  or a second device** — sealed or parked, each with its reason.
- **Any universe below large caps** (M12.1e), and any name the source
  does not serve: survivorship stays a named bias on every universe
  record.

## 4. The findings that outlast the programmes

**The lab's product is its refusals.** Six questions, one supported, and
the supported one carries beside it the record that undid its meaning.
Every refusal — a coin flip, a floor missed by 0.041, a plateau the sweep
could not hold, a pooled effect carried by one name, a winner with fewer
trades than the plan required — is in a Register with its evidence, and
none was edited away. What was learned was learned from what the guards
refused, and it is written where the next programme must read it.

**Every gate must be shown passable before alpha moves, and "shown" means
counted the way the guard counts.** The first programme learned to freeze
the calendar, measure ρ, require the seed and add a kind only by ADR. The
second learned that the screen's statistic must be the verdict's. The
third learned that a promise made from the template's signals is not the
guard's count of the winner's trades, at the cost of 0.15 alpha and a
refusal the guard was built to give. Each lesson is a guard, a stamp or a
bound now, with a test; none is a note.

**The always-long return at a geometry is a property of the era, not of
the entry.** At hold 20 inside the up regime it was +0.016 on 1993–2003
and +0.214 on 2003–2019 (#9, #24 of programme 2). No statistic on the
definition partition saw it coming. A lab that compares an entry only to
random entry can be right about chance and wrong about the market it is
in; the fifth check exists because the fourth verdict showed that.

**Numbers are declared for a shape.** The alpha split that bought two
15-cell families on grid-001 bought none of grid-002's seventeen 30-cell
candidates; a floor affordable at k = 4 is not a floor affordable at
k = 15. The Registers record what each set of numbers could buy and do
not say what the numbers should have been; that is the author's, and it
was the author's each time.

**Breadth at zero alpha is cheap and honest; depth is priced and rare.**
Two surveys of 38,976 cells each, computed on a spot burst in 47 and
about 97 minutes and torn down the same day, screened everything the
closed enum could express on four universes. From them the author
registered three questions. The ratio is the design, and the design held:
no cell was measured that was not registered, no question registered that
was not screened or drafted, no alpha spent that the ledger did not
charge first.

**What was found was found on the way.** The limit fill model, the
exhaustive fill audit and the missed-trade census (ADR-0040–0042); a
target family that could not compile; an archive that had grown under a
reproduction; an engine sha dirtied by the loop's own writes; a sentence
that denied its own gate; question ids that would have numbered one
programme's question as another's; a power promise that counted the wrong
thing. None was a verdict. Each is a record, a guard or a test, and the
S4 audit of 2026-09-21 found no normative text contradicting another.

## 5. What it cost

Alpha: 0.55 of 1.20 declared across three programmes' axes, the reserves
untouched. Data: the licensed archive at the source's free tier, 120
names, no bar in the repository. Compute: two spot bursts, torn down with
every resource verified absent. Time: fourteen days from the first
question to the third stop. Money: inside the cap recorded at M0.14, with
no execution host and no subscription; no amount is written in any
Register or page, by construction.

## 6. What would have to be true to continue

Stated as conditions, not as a recommendation, because each is a decision
the Registers do not make:

- a configuration declared for the shape of the grid it will buy from —
  the floor, the split and the falsifier count, the author's three sets
  of numbers — after `python -m occams whatif` shows what it affords;
- a measured spread, the first act of any programme that trades, never a
  recommended figure (M5.0);
- an execution host, priced and credentialed outside this lab, before any
  Strategy leaves `FORWARD` (ADR-0044);
- a publication decision recorded either way (R7), whether or not any of
  the above is taken.

## 7. The decision

None is taken here. Three programmes are stopped by record and concluded,
every conclusion adopted; nothing prepares, registers, surveys or measures
in any of the three Registers again. The publication decision is the
author's and is the last step in *Definition of done*; the publication
check (`make prepublish`) passes on every page and Register, and is the
gate's check, not the decision.

---

Drafted by the agent on 2026-09-23 on the author's instruction, from the
three Registers as they stand and the three adopted conclusions. Adopted
by the author on 2026-09-24, as written; the publication decision (R7)
is the one step of *Definition of done* that remains.

**Correction, 2026-09-24** (appended; nothing above is edited): §2 cites
record #22 for Q2-001's four passed checks. The resolved record is #19;
#22 is the Strategy's transition to `FORWARD`. Found while indexing the
Registers for `docs/INTEGRITY.md`.

**Note added 2026-10-10.** Nothing above has been edited.

In October 2026 an outside reviewer looked at the statistics behind the
five checks and found they were easier to pass than we had claimed. We
reran every point the review made, and it held up. The fixes went out in
three releases, 1.0.1 and 1.1.0 on 3 October and 2.0.0 on 4 October. The
checks are stricter now. The three Registers this statement is written
from have not changed by a single line.

That raised an obvious question: if the six questions had been judged
under the stricter rules, what would the answers have been? To find out,
each question was first rerun in the exact code that judged it at the
time, to confirm the original numbers came back. Five of the six did.
Q3-001 never reached the engine, so there was nothing to rerun. Each of
the five was then judged again with the current code, on the same data
and the same seed. The results are kept in `register/diagnostics.jsonl`
and written up in plain terms in `docs/RESCORE-2026-10.md`.

| question | original verdict | under today's rules |
|---|---|---|
| Q-003 | null | still null; four of the five checks fail it |
| Q-004 | null | still null; all five fail it |
| Q-005 | null | would not have been measured at all: 893 trades is too few for how noisy its returns are |
| Q2-001 | **supported** | **null**: it fails the floor and the fifth check |
| Q2-002 | null | still null; it fails the floor, as before |
| Q3-001 | refused before measurement | not rerun |

The one that matters is Q2-001, the only supported verdict this lab ever
produced. Under today's rules it fails. The best cell in its sweep is now
a different one from the one recorded (cell [2, 0] rather than [4, 0]):
7,642 trades averaging +0.091 R each, which is +0.054 R better than simply
being long at the same times. Once the uncertainty in that average is
allowed for, the lower bound is +0.002 R, against a floor of 0.15 R. And
the fifth check, which asks whether the entry signal adds anything over
just being long, gives p = 0.031 where 0.01 is required. Nothing that
failed a question originally passes it now, and no question comes out
better than its original verdict.

What this does not change. The Q2-001 verdict stays "supported" in the
Register, because that is what the rules in force at the time said, and
sealed records are never rewritten. This note sits beside it. The
falsifier count, the alpha spent and every number in §1 are as they were.
The lab is still closed: nothing will be registered or measured in these
three Registers again. And this note is not a verdict. It is a reading of
the old questions under new rules, written down so that nobody has to
take the one supported verdict at face value.

One known gap remains. On the multi-day engine, when the names in a
universe move together with the market, the beats-null check still passes
a little more often than it should at the 5% level. Every question in
this lab was run at the 1% level, where it behaves. The gap is recorded in
ADR-0048.
