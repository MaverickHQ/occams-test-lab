---
status: adds a standing check beside ADR-0014's null harness
---

# The apparatus must prove it can accept, not only that it can refuse

The failure this design is built against is the vacuous pass — a guard that
passes because it was given nothing to look for. It appeared eight times in
the donor programme. `make null` exists to catch it, and is promoted to
standing check S3: a coin-flip strategy driven through the whole pipeline
must be **refused**.

The symmetric failure has no check at all. Four conservative gates, all of
which must pass, compose multiplicatively. **A pipeline that refuses
everything satisfies every test in this specification** — and satisfies S3
*more* comfortably the more broken it is. A check that gets easier to pass as
the system degrades is not a check.

**A second known-answer probe is therefore required.** A synthetic series
carrying a **planted effect of declared size** must reach `FORWARD`, with all
four checks passing, and it runs in CI beside the null as standing check S10.

The planted size is declared in the same units as the floor — EV per trade in
net R together with a trade frequency — and is set **at or just above the
declared floor**, so the probe measures sensitivity at the boundary that
actually matters. Neither probe is a Hypothesis and neither spends alpha;
they are apparatus tests, registered at alpha 0 as the calibration campaign
is under D23.

## Considered options

- **Rely on the four per-guard tests (M2.5).** Each isolates one refusal
  while the other three pass, which proves wiring. The risk is not in any one
  guard, it is in their **composition** — four individually reasonable
  thresholds that are jointly unsatisfiable. No per-guard test can see that.
- **Treat the first real strategy reaching `FORWARD` as the evidence.**
  Cheapest, and it conflates two very different outcomes: if nothing ever
  passes, there is no way to tell whether there was no edge or the machine
  cannot say yes. That ambiguity is unrecoverable, and it arrives after the
  budget has been spent finding it.
- **Plant a large, obvious effect.** Easy to pass and nearly worthless — it
  would clear gates that remain far too strict at any realistic effect size,
  which is the failure being guarded against.
- **Make it advisory rather than blocking.** The same decay as a soft alpha
  budget under ADR-0011: nothing ever fails, and the discipline quietly
  stops meaning anything.

## Consequences

Two standing checks now bracket the pipeline from both sides — **S3**: the
null is refused, naming which refusal fired; **S10**: the planted effect is
accepted, naming that all four passed. A gate change that breaks either is
caught at the commit that caused it rather than at the first real verdict.

**S10 must run at a sample size the power calculation shows is adequate**
(M0.15). Otherwise a failure is ambiguous between "the gates are too strict"
and "this effect is undetectable in this many trades", and the probe would be
testing two things at once.

**A failing S10 does not automatically mean loosen the gate.** It means the
apparatus cannot detect an effect of the size declared as worth having, which
is a finding about the programme, not a defect to be tuned away. The
resolution may legitimately be a higher declared floor, more data, or a
recorded stop.

The planted effect's size and frequency are configuration, not constants in
code — the floor they track is the author's (R9 reasoning).
