---
status: decided · the shape is already here; the keep rule and the never-ask directive are refused; one consequence for M8
---

# Autoresearch: the shape is adopted, the keep rule is refused

Asked on 2026-09-10, after the author's numbers went in: can Karpathy's
`autoresearch` be used as an option in this lab? The repository was read
(README and `program.md`, MIT licence). It is an agent loop: edit one
file, train for **a fixed five minutes**, read one metric, and apply one
rule — *"If val_bpb improved (lower), you 'advance' the branch, keeping the
git commit. If val_bpb is equal or worse, you git reset."* Results go to an
append-only `results.tsv`; `program.md` is the human-curated instruction
file; the agent is told *"Do NOT pause to ask the human if you should
continue"* and to run indefinitely. About a hundred experiments a night.

**Its shape is this lab's shape, and was before the question was asked.**
A fixed budget per experiment is a fixed alpha per question and a fixed N
per cell (R4.4, M0.15). The append-only results file is the hash-chained
Register, which also records every discard as a refusal with its evidence
(N6). `program.md` is `CLAUDE.md` and the proposer's declared constraints.
An agent that may touch only `train.py` is a proposer that may emit only
Drafts, in a sandbox enforced by type (D15, M7.4).

**Its rule is the failure this lab exists to refuse.** Keeping the best of
a hundred looks at the same validation set is a search of size one hundred
charged as one — the donor's search-corrected 1.70, automated and run
overnight. The rule works for a language model because `val_bpb` is
measured on millions of tokens, so run-to-run noise is small beside a real
improvement, and a false improvement costs a slightly worse model that
tomorrow's run replaces. Here the standard error per experiment is about
0.04R against a 0.15R floor at a thousand trades, a false discovery costs
real money, and the alpha it spends does not come back (ADR-0011). The
search correction is the price of running this loop on markets, and the
price is what makes a hundred a night unaffordable: screening a hundred
variants before registering one is `search_space_size = 100`, which takes
the required N per cell at a 0.15R floor from about 750 to about 1,400 and
a single question's spend past the whole runnable budget.

**Its autonomy directive is the alpha-drain attack.** "Do not ask the
human; run indefinitely" is the exact inverse of R4.8 and ADR-0016: an
agent that registers without asking can close an axis permanently, and an
agent that never stops has no falsifier (ADR-0033). The lab declares when it
stops; autoresearch declares that it does not.

## Decision

- **The shape is adopted, and it is already built.** Nothing in
  autoresearch's structure is missing from this repository; the mapping
  above is one-to-one.
- **The keep rule is refused.** Keep means: beats random entry at the
  Bonferroni-corrected alpha, clears the floor declared before running,
  holds a plateau, survives leave-one-out — all four, evaluated once, with
  every discard recorded (DESIGN §3, M2.5).
- **The never-ask directive is refused.** Registration is a human's act
  (R4.8); the number of resolved mechanism verdicts at which the lab closes
  is declared before the first one (ADR-0033).
- **One consequence for M8**, recorded as a task: measurement is
  deterministic, so a queue of *already-registered* Hypotheses may run
  unattended — propose, human registers, measure at fixed N, verdict,
  append — and only registration needs the author awake. That is the
  autoresearch rhythm with its two corrections in place.

## Considered options

- **Run the loop as-is on backtests, with the Register as the results
  file.** The most direct reading of the question. Rejected: it is a search
  of a hundred charged as one, and every kept "improvement" is the maximum
  of noise plus signal on a holdout that has now been looked at a hundred
  times. The reserve's one look per hash (ADR-0006) would be spent on the
  first night.
- **Run the loop as a proposer that pre-screens drafts on the definition
  period.** Tempting, because the definition period is excluded from
  measurement. Rejected as a default: screening on price data is a search
  and must enter `search_space_size` and the consumed-observation record
  (M6.6), at which point the arithmetic above applies. Drafting from
  mechanism reasoning, with no price data touched, is what a proposer
  already is and costs nothing (R4.6).
- **Run the loop on the apparatus, not the market.** Engine speed against
  the hand-checked fixtures, the synthetic controls' sensitivity at the
  boundary, fixture coverage. Allowed today; low value; not what was asked.
- **Adopt the loop's rhythm for registered questions only.** Taken, as the
  M8 consequence above.

## Consequences

An `occams loop` driver at M8 runs the registered queue unattended: for
each Hypothesis in REGISTERED, measure at the declared N on the measurement
partition, evaluate the four refusals, append the verdict or the refusals,
advance. It never registers, never touches the reserve, and stops when the
queue is empty or the falsifier fires. `program.md`'s role is `CLAUDE.md`'s,
and stays there.

The general rule, which outlives this repository as ADR-0034's did: **an
optimisation loop transfers to this lab exactly to the extent that its keep
rule is a corrected test and its budget is counted in looks, not minutes.**
