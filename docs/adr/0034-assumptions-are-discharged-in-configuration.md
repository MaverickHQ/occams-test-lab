---
status: decided · revisit trigger named below, not left open-ended
---

# Assumptions are discharged in configuration, not in a proof assistant

**Disambiguation first, because this project has been caught by a name twice.**
*Lean* here means **Lean 4**, the theorem prover and implementation of
dependent type theory. It is **not** *LEAN*, QuantConnect's
algorithmic-trading engine, which is what the word means almost everywhere
else in this domain. Anything written here about "Lean" says nothing about
that engine, which is a separate question for **M0.9**.

## The argument

Formal verification proves that an **implementation matches a specification**.
It is silent on whether the specification is true of the world.

That distinction decides this, because **the failures this project has
actually recorded are validity failures, not correctness failures**:

- **A4.** The 500-day parity check passed *because engine and renderer shared
  the same wrong assumption*. Two implementations, mutually consistent, both
  wrong. A proof would have established their equivalence — correctly, and to
  no purpose.
- **ADR-0029.** A pipeline that refuses everything satisfies every test in
  this specification, and satisfies S3 more comfortably the more broken it is.
  There is no correctness property to verify; the whole defence is the
  positive control.
- **ADR-0014.** Forward testing falsifies. The reason is epistemic — unseen
  wall-clock data — and no amount of proof substitutes for it.

The apparatus this project builds — pre-registration, the sealed reserve, the
declared floor, the null harness, the positive control — exists because
**the hard problem here is epistemic, not computational.** A proof assistant
is an excellent tool for the problem this project does not have.

## The exception, and it is real

One failure class does fit, and it has now occurred twice.

- **A5.** The donor's Monte Carlo is valid *because days are independent*.
  Multi-day holds break it **silently**.
- **2026-09-10.** M0.15's power formula counted trades as independent
  observations. Calendar-clustered entries are not:
  `N_eff = k / (1 + (k - 1) * rho)`. Same failure, different decade, found by
  accident while drafting something else.

Both are statistical results resting on an assumption nobody was tracking,
and **that is exactly what dependent types are for** — making an assumption a
proof obligation rather than a comment, so a call site that cannot discharge
it does not compile.

The lesson is real. The tool is not the only way to take it.

## Decision

**Assumptions are discharged as declared parameters with recorded
provenance**, in configuration and in the register, not as proof obligations
in a type system. `sigma` and `rho` are the first two and M0.15 already
carries the pattern: a declared value, its provenance, and — where it is
declared before it can be measured — a **range** across which the go/no-go
must hold.

**No proof assistant is a build, test or CI dependency of this project, in v1
or after.** That half is not deferred; it is decided.

## Considered options

- **Lean 4 as the implementation language.** Discards the vendored core —
  2,412 lines, *"the part that took a year to get right"* (DESIGN-v4 §8) —
  and there is no market-data ecosystem to replace what it would throw away.
  The learning curve competes directly with M0, which is the binding
  constraint on this project and has been for weeks.
- **Verify a Lean model of the Python.** Rejected on the strongest available
  evidence: **it recreates A4.** A proof about the model and a bug in the
  implementation, the two agreeing on a wrong assumption, is the exact
  failure the parity check already demonstrated once.
- **Typed known-at instants.** The highest-severity silent bug class in the
  design, and a genuine fit. Rejected on margin, not on merit: a Python
  `NewType` plus an assertion at the boundary catches most of it at a
  fraction of the cost. The Lean version is stronger; it is not
  proportionately stronger.
- **Verify the alpha algebra offline as a one-off design artifact.**
  **Not rejected — deferred with a trigger** (below). The invariant
  `sum(axis) + reserve == total`, monotone decrement, exhaustion terminal
  until new data, reserve at-most-once per spec hash. **A1 shows this is not
  hypothetical**: the donor's register carried a raw 0.620 against a
  search-corrected 1.700, a state the budget forbids, and it shipped.
- **Do nothing about assumptions.** That is A5, twice. Rejected by the
  evidence above.

## Consequences

**The revisit trigger is named, not open-ended.** The alpha-algebra proof
becomes worth its cost **after M1 ships and if the algebra proves fiddly in
practice** — meaning a real inconsistency, or a rule change whose effect on
the invariant is not obvious by inspection. At that point the rules are
stable and load-bearing, which is when a one-off proof is cheapest and worth
most. Before then it is optimising a stage this project has not reached.

**It stays an artifact, never a dependency.** Even if adopted, no build step,
test or CI check may require it. A proof that gates the build is a proof that
gets deleted the first time it blocks a release.

**The general rule, which outlives Lean.** *A tool that improves correctness
without improving validity ranks behind the M0 gates.* Type checkers,
property-based testing, fuzzing, static analysis and model checking all fall
under it. None is discouraged where cheap; none justifies delaying a free
lookup that can stop the project.

**What this does not say.** It does not say formal methods are unsound or
unhelpful. It says this project's bottleneck is elsewhere, and that spending
the scarce resource — the author's time — on correctness while validity and
affordability remain unmeasured would be the same mistake in a more
respectable dialect.

**Naming, if it is ever adopted.** Disambiguate from QuantConnect's LEAN on
first mention, in the ADR that adopts it and in `CLAUDE.md`. The naming trap
has caught this project twice and both times it was a collision nobody
thought worth writing down.
