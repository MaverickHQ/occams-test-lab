---
status: decided 2026-09-17 — drafted after Q2-001 resolved supported (#19) with its shrinkage record beside it (#24) and adopted by the author the same day; built: `Measurement.baseline_ev`, `guards/beats_always_long.py`, five names in `forward.CHECKS`, both engines and the synthetic control supply the distribution, a verdict names the checks it was judged against, `prepare` shows the baseline on the definition partition; binds from the next registration; Q2-001 is not re-judged (M12.12 closed). Found in the build: the day-boxed signal control planted a drift on every day and entered always-long — the very shape this check refuses — so it now plants its return on the day after two lower closes only and enters by a down-run, at the floor after the spread; `make null` refuses and `make signal` accepts on both engines
---

# Beating always-long at the same geometry and gate is the fifth check

DESIGN §3 makes GOOD SETUP? four refusals, all evaluated, all recorded:
the plateau, beats the null, clears the declared floor, leave-one-out
(`occams/guards/forward.py`). On 2026-09-17 the second programme's first
question, Q2-001 — *after four consecutive lower closes, an S&P 100
constituent carries positive EV over the next bars, inside the up regime
of the classifier frozen on SPY* — passed all four on the measurement
partition: the winner (hold 20, stop 2 %) at EV +0.213 net R over 6,946
trades, 412.7 a year, bounded costs (#19). The Strategy is at `FORWARD`.

The record appended beside it says something the four checks cannot.
M12.6's `Shrinkage` (#24) runs always-long at the winner's geometry and
gate — a market order on every box, long, the same hold, stop, horizon
and regime gate, no entry signal at all — on the same partition, and it
makes **+0.214**. The margin is **−0.001**. On the survey's definition
cell the same comparison had given +0.239 (EV +0.256 against always-long
at +0.017, #9). Read together: on the sixteen years the verdict was
measured on, waiting for four down days before buying did exactly as
well as not waiting. What the verdict measured is being long S&P 100
names inside the up regime for twenty bars with a 2 % stop. What the
mechanism sentence claims is the streak. The two are not the same
hypothesis, and the four checks passed the second on the strength of
the first.

**Why the four could not see it.** Beats-null draws its null as random
entry with a coin-flip side — long and short, a seeded coin per box
(`position_boxed.null_distribution`, `day_boxed` alike) — block-
bootstrapped over positions in time order. That null asks *better than
chance?*; a long-only strategy inside a rising, gated partition answers
yes without its entry signal doing anything. The floor is absolute (0.15
R, 50 a year) and asks *big enough?*. The plateau and leave-one-out ask
*a region, not a spike?* and *not one name?*. None asks *better than the
passive alternative at the same geometry?* — which is the question the
survey's trust tiers ask of every cell (held, positive, margin; M12.3,
M12.4) and the reason M12.6 records the margin per verdict. M12.6 called
the recorded diagnostics "a gate only if the author declares it". This
is that declaration, drafted for the author.

## Decision (adopted 2026-09-17)

1. **A fifth check, `beats_always_long`.** The winner cell's EV must
   exceed the distribution of always-long at the same geometry and
   gate at the Bonferroni-corrected alpha: random entry *days*, long
   side only, the same exits, stop, horizon and regime gate, a market
   order on every box, positions in time order, block bootstrap over
   them — the construction beats-null already uses, with the side fixed
   to long instead of a coin. The same thinness rule applies: a
   distribution with too few draws to resolve the corrected alpha is
   refused, not passed. Refusal text, in the Register's voice:
   *beats-always-long: being long at the same geometry and gate does as
   well*; evidence: `p_baseline`, `alpha_corrected`, `winner_ev`,
   `baseline_mean`, `draws`.
2. **The contract carries it.** `Measurement` gains `baseline_ev:
   tuple[float, ...]`, the Monte Carlo EVs of always-long, beside
   `null_ev`. The guards read `occams/measurement.py` and nothing else
   (CLAUDE.md); an engine that cannot supply the field is not an engine.
   Both real engines compute it from the `ALWAYS`/`LONG` probe exactly as
   `null_distribution` computes the coin-flip probe. The synthetic
   engine draws it as the means of `−cost + σ·z`: under no drift its
   always-long *is* its null, so `make signal` (a planted effect at the
   floor) passes the fifth check and `make null` (a coin flip) is
   refused as before. **S3 and S10 hold after the change or the change
   does not land.**
3. **Same gate, deliberately.** For a regime-gated question the baseline
   is long inside the regime, so the check attributes the effect to the
   entry rather than to the gate. The gate's own value — whether the
   classifier times the market — is a different question, one the
   regime axis has never registered, and this check does not pretend
   to answer it.
4. **Shown passable before alpha moves.** `question prepare` shows the
   always-long baseline on the definition partition beside the cell's
   EV — from a survey it already prints the survey's margin and tier;
   from a Draft it computes the same probe — so the fifth gate meets
   M12's rule that a gate is shown passable before anything is spent.
   The survey's gate readiness is unchanged: *held* and *positive*
   already require a positive margin on the definition partition.
5. **From the next registration, never backwards.** A verdict is a
   one-time resolution under the checks the question was registered
   with (ADR-0036; "changing the checks after a verdict is a recorded
   decision, not a re-run", M6.2). Q2-001 stands as recorded: supported
   by four checks, with the margin the fifth would have refused written
   beside it (#24). Re-asking it is a new registration under five
   checks, costs alpha, and is the author's act; the R4.9 distinction
   is that the fifth check is now declared.
6. **The record names five.** `forward.CHECKS` gains the fifth;
   `HypothesisResolved.refusals` carries its sentence when it fires;
   the passes list, the console card and the programme page show five;
   a refusal by this check is a null verdict and counts toward the
   falsifier like any other.

## Consequences

- `occams/measurement.py` (`baseline_ev`), both real engines and the
  synthetic engine (the probe and the draws), a new
  `occams/guards/beats_always_long.py`, `forward.py`'s tuple, the
  controls' assertions ("all five checks passed"), DESIGN §3 ("five
  refusals"), the console's and programme page's check lists. Tests: a
  fixture whose signal equals always-long at its geometry is refused by
  name and one whose signal exceeds it passes; the existing four-check
  fixtures gain a baseline; the synthetic control names five.
- The engine code hash changes; the survey's cells are not recomputed
  (the survey does not run the guards) and a later grid carries the new
  hash.
- Alpha is untouched: a check is not a cost. The `Shrinkage` record
  stays as it is — the definition margin beside the measured margin —
  and the check's p-value becomes part of the verdict's evidence rather
  than a diagnostic after it.
- A supported verdict now attests that the entry beat the passive
  alternative at its own geometry and gate on a partition nobody read
  first. That is the claim the mechanism sentence makes, and the claim
  the forward window (ADR-0014) would then falsify or not.

## Considered options

- **Keep it a diagnostic (the status quo).** The margin stays recorded
  beside every survey verdict and is not a gate. Rejected in this
  draft: a verdict would then attest the gate and the side while the
  sentence claims the entry, and the lab's stated purpose is that the
  sentence and the test agree. Kept as the author's alternative: nothing
  is wrong in the Register, and the record is legible either way.
- **Change beats-null's null to long-only.** Rejected: it changes the
  meaning of a check four verdicts resolved under, and it loses the
  two-sided null, which still answers a question worth asking — better
  than chance in either direction. Two nulls test two things; the
  Register can say which one refused.
- **A point-estimate margin floor (margin ≥ X R).** Rejected: a
  threshold with no significance behind it, and a new author's number.
  The Monte Carlo at the corrected alpha needs no new number and refuses
  when it cannot resolve.
- **Margin at or above the declared floor.** Rejected: it doubles the
  floor's meaning. The floor is absolute EV, declared for the money's
  sake (M0.15); this check is attribution, and the two should be
  refused separately so the Register says which.
- **Apply it to Q2-001 now.** Rejected: a verdict is one-time; the
  checks are stamped at registration; and the record already carries
  what the fifth check would have said. A lab that re-judges a verdict
  under a rule written after seeing it is the thing every gate here
  exists to prevent.
