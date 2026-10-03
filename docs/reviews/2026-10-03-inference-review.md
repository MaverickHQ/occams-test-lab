# occams-test-lab — FIXES-AND-TESTS

> **Published copy, 2026-10-03.** An external review of this repository at
> `2e86d58`, written as the defect catalogue of the successor lab and
> committed here on the author's instruction (`TASKS-v4.md` M16.2). Two
> sentences are reworded where this repository's publication gate requires,
> each marked in place; nothing else is changed. What was checked and what
> reproduced is in
> [2026-10-03-inference-review-verification.md](2026-10-03-inference-review-verification.md).
> What this lab does about each fix — built here in three releases, or left
> to the successor with the reason — is M16 in `TASKS-v4.md`. Where this
> text and M16 differ, M16 is what was done.

| | |
|---|---|
| Repository | `MaverickHQ/occams-test-lab`, package `occams` v1.0.0 |
| Commit reviewed | `2e86d58` (HEAD, 2026-10-03 16:09 +0100); donor `prop-challenge-lab@cfc5af8` |
| Date | 2026-10-03 |
| Scope | `occams/` (15.8k LOC), `tests/` (7.9k), `tools/`, `scripts/`, `register/*.jsonl`, `docs/`, CI. Read-only review. The verdicts were **not** re-run (the licensed archive and `occams.toml`/`configs/` are not in the public tree). |
| Baseline on this commit | `pytest`: about 652 tests pass (about 5.5 min full; about 75 s with `-m "not slow"`). `ruff`, `credscan`, `prepublish` and `vendor_core --verify/--verify-donor` are clean. All 6 Registers verify, and their heads match `docs/LAB-CONCLUSION.md`. `make null` and `make signal` behave as documented on both engines. |

**Evidence legend.**
- **[V]** means read in the code or Register at this commit, with file and line given.
- **[V-probe]** means measured by a probe script run against this commit. The scripts are in Appendix A, so you can re-run them.
- **[I]** means inferred. Each [I] item says what would confirm it.

**Severity legend.**

| Severity | Meaning |
|---|---|
| **P0** | Correctness of verdicts. The test a guard performs is not the test it claims, or its error rate is not the declared alpha. |
| **P1** | Integrity and governance: the Register, the alpha ledger, identity of the code that measured, and the apparatus's own calibration. |
| **P2** | Realism: what the simulators and data assume about the market. |
| **P3** | Hygiene and docs. |

**Idiom.** Every fix is `OTL-Fnn`. Every task is `OTL-Tnn`. Every test is written **red first**: the doc names at least one test per fix that FAILS on `2e86d58` and passes after the fix. A test marked `@slow` runs in `make check` and in CI, never in `make test-fast`. Refusals are loud and named. No fix introduces a default for an author's number (R9). Where a fix needs a new number (a confidence level, a ceiling), it is a required config key with no default, and `python -m occams --schema` prints the key and never a value.

---

## 1. Governance — how fixes reach a lab whose verdicts are sealed

Six rules, to be adopted as **ADR-0047** before any code in §3 lands.

**G1 — Fixes bind forward, by ADR.** Each P0, P1 and P2 fix is adopted by an ADR and binds from the next registration onward, as ADR-0043 and ADR-0045 did. Reserve the range **ADR-0047 to ADR-0060**:

| ADR | Title (proposed) | Fixes |
|---|---|---|
| 0047 | Fixes bind forward; re-scores are diagnostics, never verdicts | governance (this section) |
| 0048 | The null is drawn at the winner's N, by calendar date, with p counted plus one | F01, F02, F03 |
| 0049 | The fifth check is side-matched and dependence-aware; execution is paired, selection is randomised | F04 |
| 0050 | The floor is cleared by a lower confidence bound; power is planned against a declared alternative | F05, F06 |
| 0051 | A plateau is judged in standard errors, without the winner in its own median | F07 |
| 0052 | A survey ranks under a max-statistic null; screen, validate, then measure | F08, F18 |
| 0053 | Overlap is structural, and the lab has one alpha ceiling | F09, F10 |
| 0054 | The Register's heads are pinned, signed and anchored outside the repository | F11, F12 |
| 0055 | The engine is identified by content; a dirty tree cannot measure | F13, F14 |
| 0056 | A universe is point-in-time, or it carries a measured survivorship diagnostic | F15 (amends ADR-0025) |
| 0057 | Costs are measured or swept; stops pay slippage | F16 (amends D23 / M5.0's closure) |
| 0058 | The calibration gate runs on every engine before it measures | F17, F23 |
| 0059 | Entry kinds are modules in a closed registry | F21 (amends ADR-0037) |
| 0060 | reserved | — |

**G2 — Sealed verdicts are never edited.**
- No line of `register/register.jsonl`, `programme-2.jsonl` or `programme-3.jsonl` is rewritten.
- No closed Register gains a record. `occams/stopping.py:10-13`: "After any stopping record nothing prepares, registers, surveys or measures in that Register".
- `HypothesisResolved` keeps its outcome for ever.

**G3 — A re-score is a diagnostic, in its own store.**
- Add `register/diagnostics.jsonl`. It is a new `Store` subclass with its own chain and one record kind, `Rescored`:
  ```
  Rescored(hypothesis_id, register_path, annotates_seq, annotates_sha,      # the record it annotates, by chain sha
           adr: tuple[str, ...], engine_sha, engine_code_sha, seed,
           reproduced: bool,                   # the original numbers recreated first, exactly
           checks: tuple[str, ...], refusals: tuple[str, ...],
           outcome_under_rules: str,           # what the named ADRs would have said
           evidence: dict)                     # p-values, SE, LCB, sigma, N — every number, passing or failing
  ```
- It never counts toward the falsifier (`occams/falsifier.py:22-30` reads `HypothesisResolved` only — keep it so), never spends or accrues alpha, and never changes a balance.
- The console and the programme pages render it **beside** the verdict it annotates ("as reached: supported · under ADR-0049/0050: refused, floor LCB 0.099"), never in place of it.
- Use a separate store, rather than annotating inside a closed Register, so G2 holds literally.

**G4 — Re-score at a clean commit.** The stamped verdict commits are **not in the public repository** [V]: `git cat-file -e` fails for `e2cdf14` (Q-003), `b145d49` (Q-004), `e05a659` (Q-005), `1a243e5` (Q2-001) and `8f81ff3` (Q2-002). `reproduce private --at-commit` (`occams/reproduce.py:175-188`) therefore fails "cannot check out" on the public tree. The procedure runs in the author's **private history repository**, beside the licensed archive:
1. `python -m occams reproduce private --question Q2-001 --register register/programme-2.jsonl --queue register/programme-2-queue.jsonl --archive archive --config configs/programme-2.toml --at-commit`
   - It must print an exact reproduction: N, winner cell, EV to 1e-12, refusals.
   - If it cannot, the re-score stops and records `reproduced=False` with the reason. Never re-score what you cannot first reproduce.
   - Both P2 verdicts carry `-dirty` stamps (`programme-2.jsonl` #15, #19, #28, #33). `compile.py:136-142` attributes this to the loop's own Register writes. Reproduction at the bare commit is then the test of that claim.
2. Check out the clean commit that implements the ADRs being applied. `git status --porcelain -- occams tools pyproject.toml` must be empty (F13).
3. `python -m occams reproduce private --question Q2-001 … --rules 0048,0049,0050 --diagnostic register/diagnostics.jsonl`.
   - This is a new flag. It re-measures with the **same seed, same partition and same sweep**, evaluates the guards under the named ADRs, and appends one `Rescored`.
   - It refuses if the diagnostics store's head is not the pinned head (F11).
4. Commit `register/diagnostics.jsonl` and the updated `register/HEADS.toml`, then sign the heads (F11).

**G5 — Conservative fixes before non-conservative ones.**
- A *conservative* fix can only turn passes into refusals (F01, F02, F03, F05, F06, F08, F09, F10).
- A *non-conservative* fix can move numbers either way (F15 point-in-time universes, F16 measured costs, the paired execution part of F04, and F07's slack).
- Land and re-score the conservative bundle first. Re-score the non-conservative fixes **only on top of it**, never on a guard set already known to be anti-conservative.
- Every `Rescored` names its full ADR set.

**G6 — The apparatus proves itself before and after every fix.**
- `make null` and `make signal` on both engines (S3, S10).
- The new size and power table (F23) runs before and after each P0 fix.
- A fix that leaves any guard's measured size above `α + 2.33·sqrt(α(1−α)/S)` over `S ≥ 200` seeds is not done.

---

## 2. Summary of fixes

Column 6 asks: does this change recorded numbers? **No** means displays, records or refusals only. **Numbers move** means p-values, SEs or EVs change but no outcome is expected to flip. **Verdict at risk** means a recorded outcome or readiness table could change under a G3 re-score.

| ID | Title | Sev | Files | Effort | Changes recorded numbers? |
|---|---|---|---|---|---|
| OTL-F01 | position_boxed null and always-long baseline resampled at the pool's N, not the winner's | P0 | `engine/position_boxed.py:163-219,253-255`; `survey/candidates.py:403-405` | S | Numbers move (Q-005, Q2-001, Q2-002 p-values; readiness) |
| OTL-F02 | Nulls ignore same-date dependence; position_boxed blocks on per-name bar index | P0 | `engine/day_boxed.py:331-338,361-369`; `engine/position_boxed.py:198,217` | M | Numbers move |
| OTL-F03 | Monte Carlo p without +1; passing evidence never recorded | P0 | `guards/beats_null.py:26-27`; `guards/beats_always_long.py:30-31`; `survey/candidates.py:412`; `guards/forward.py` | S | Numbers move (tiny) |
| OTL-F04 | Fifth check is side-blind and dependence-blind (a coin flip passes it) | P0 | `guards/beats_always_long.py`; engines' baseline functions | M | Verdict at risk (Q2-001, diagnostic only) |
| OTL-F05 | Floor judged on the winner's point estimate | P0 | `guards/clears_floor.py:14`; `hypothesis.py:70-75`; `core/power.py` (call sites only) | M | **Verdict at risk (Q2-001)** |
| OTL-F06 | Power promised at the template's σ, not the winning cell's | P0 | `guards/measure.py:16-27`; `survey/candidates.py:318` | S | **Verdict at risk (Q2-001)** |
| OTL-F07 | Plateau slack is absolute and the winner sits in its own median | P0 | `guards/plateau.py:30-32` | S | Numbers move |
| OTL-F08 | Survey's fifth check is selection-blind over 38,976 cells; no validate step; "halves" wording | P0 | `survey/candidates.py:349-419`; `survey/run.py`; `README.md:128,134,178,189` | L | Verdict at risk (grid-001/002 readiness tables) |
| OTL-F09 | Overlap gate bypassed by any free-text distinction and by a change of axis | P1 | `ledger/alpha_budget.py:223-259`; `survey/candidates.py:343,710` | M | No |
| OTL-F10 | Accrual outside the declared total; no lab-wide alpha ceiling | P1 | `ledger/alpha_budget.py:134-140,195-205`; `config.py` | M | No |
| OTL-F11 | Register is a keyless chain: forgery and truncation verify; heads pinned nowhere | P1 | `register/store.py:103-130`; new `register/HEADS.toml`; `tools/prepublish.py` | M | No |
| OTL-F12 | Append is unlocked and quadratic | P1 | `register/store.py:97-136` | S | No |
| OTL-F13 | Engine identity: `-dirty`/`unknown` accepted; content hash covers a hand list missing fills, sizing, guards | P1 | `core/archive.py:97-106` (vendored, wrap only); `spec/compile.py:136-164`; `survey/run.py:47-59` | S | No |
| OTL-F14 | Stamped commits absent from the public history; at-commit reproduction impossible | P1 | `reproduce.py:175-200`; new `SOURCES.toml` | M | No |
| OTL-F15 | Survivorship: current-member universes measured on 1993–2019 | P2 | `data/universe.py`, `data/partitions.py`, `UniverseDeclared` | L | **Verdict at risk (Q2-001, either direction)** |
| OTL-F16 | Costs are a declared bound never measured; stops fill at the level | P2 | `costs/equity.py:53-58`; `engine/day_boxed.py:250`; `engine/position_boxed.py:107` | M | Numbers move (Q2-002 knife-edge on a point floor) |
| OTL-F17 | Vendored calibration gate unused | P2 | `core/calibration.py` (vendored, unused); new `occams/calibrate.py` | M | No |
| OTL-F18 | Baseline non-stationarity: definition is the oldest 30 % | P2 | `survey/candidates.py` readiness; `survey/run.py:220-225` (`_eras`) | S | Verdict at risk (readiness) |
| OTL-F23 | Controls show "refused once", not the guards' false-positive rate | P1 | `tests/test_controls.py:45-54`; `controls.py`; `controls.toml`; CI | M | No |
| OTL-F19 | Dead vendored modules; boto3 path reachable | P3 | `occams/core/*`, `PROVENANCE.json`, `tests/test_provenance.py` | S | No |
| OTL-F20 | Probes and the fifth check duplicated across engines and survey | P3 | `engine/day_boxed.py:306-369`; `engine/position_boxed.py:188-225`; `survey/candidates.py:349-419` | M | No |
| OTL-F21 | Entry kinds are an if/elif chain across engines | P3 | `engine/day_boxed.py:123-170`; `engine/position_boxed.py:27-28`; `spec/spec.py` | M | No |
| OTL-F22 | Stale strings | P3 | `Makefile:48`; `controls.toml:18`; `README.md:128,134,178,189` | S | No |
| OTL-F24 | Lint too narrow; small smells | P3 | `pyproject.toml`; `ledger/alpha_budget.py:25,32`; `guards/leave_one_out.py:23-26` | S | No |
| OTL-F25 | TASKS diary and CLAUDE.md size | P3 | `TASKS-v4.md`, `CLAUDE.md` | M | No |

F23 sits with the P1s because it is the apparatus's own calibration, and it would have caught F01, F02 and F04.

---

## 3. The fixes

### OTL-F01 — the position_boxed nulls are resampled at the pool's N, not the winner's (P0)

**Problem [V].** `day_boxed` resamples its null and baseline with `n_trades=max(winner.n, 1)` (`engine/day_boxed.py:401-402`). `position_boxed` does not.

```python
# engine/position_boxed.py:171-176  block_bootstrap_means(x, ...)
n = x.size
...
idx = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(draws, -1)[:, :n]
return x[idx].mean(axis=1)
```

- `null_distribution` (`:188-200`) feeds it **every random-entry position** in the partition.
- `baseline_distribution_of` (`:213-219`) feeds it **every always-long position**.
- Each draw is therefore a mean over the pool's size, not over `winner.n`, and its spread is about √(N_pool/N_winner) too narrow.
- The survey repeats the defect for multi-day cells (`survey/candidates.py:403-405`).

**Why it matters [V-probe].** Probe A1 (Appendix A) uses a pure martingale world: 8 names, 1,260 days, σ 2 %/day, zero costs, a single cell (k = 1), `down_run(3)`, hold 5, 200 seeds. Winner N is about 645 against a random-entry pool of about 2,035.

| | α = 0.01 | α = 0.05 |
|---|---|---|
| beats-null false-positive rate, as built | **0.140** | **0.225** |
| beats-null, resampled at the winner's N (F01 only) | 0.015 | 0.100 |
| beats-always-long false-positive rate, as built | 0.065 | 0.135 |

- At the lab's per-cell α of 0.01, the position_boxed beats-null fires 14 times as often as declared.
- F01 alone brings α = 0.01 inside Monte Carlo tolerance (0.015 ≤ 0.026).
- F01 leaves α = 0.05 at 2×, which is F02's job.
- Programme 1's Q-005 and both programme 2 verdicts were measured on position_boxed (`HypothesisMeasured` #26; P2 #15, #28).

**Fix.**
```python
def block_bootstrap_means(x: np.ndarray, *, block: int, draws: int, seed: int, n: int | None = None) -> np.ndarray:
    """... each draw concatenates blocks to length n (default: len(x)) and takes its mean."""
```
- `null_distribution(..., n_trades: int)` and `baseline_distribution_of(trades, *, n_trades: int, ...)` must pass `n=n_trades`.
- `measure()` passes `n_trades=winner.n` (`:253-255`).
- Add `null_n: int` and `baseline_n: int` to `Measurement` (defaults 0 for old pickles; `measurement.py:89-93`).
- The two guards refuse loudly when `m.null_n not in (0, m.winner.n)`, with the reason "the null was not drawn at the winner's N (ADR-0048)".
- Survey: `candidates.py:405` passes `n=int(row["trades"])`.

**Tests** — `tests/test_null_sizing.py` (new):
- `test_block_bootstrap_means_takes_target_length` — **RED.** It calls `block_bootstrap_means(x, block=1, draws=4000, seed=1, n=100)` on `x` of length 10,000 with sd 1, and asserts `0.09 < np.std(out) < 0.11`. Today the keyword is rejected; ignoring it gives sd ≈ 0.01.
- `test_position_boxed_null_is_drawn_at_winner_n` — **RED.** On a fixture world it asserts `m.null_n == m.winner.n == m.baseline_n`.
- `test_guards_refuse_a_null_not_at_winner_n` — **RED.** A hand-built `Measurement` with `null_n=2*winner.n` must be refused by `beats_null.check` and `beats_always_long.check`, naming ADR-0048.
- `test_survey_multi_day_fifth_check_uses_cell_n` — **RED.** It monkeypatches `block_bootstrap_means` to capture `n`, runs `fifth_check_readiness` on a two-cell fixture, and asserts `n == row["trades"]`.
- `@slow test_position_boxed_beats_null_size_at_001` — **RED today (0.140), GREEN after F01.** Probe A1 as a test with S = 200: false-positive rate at 0.01 ≤ 0.026.
- `@slow test_position_boxed_beats_null_size_at_005` — **RED until F01 + F02.** False-positive rate at 0.05 ≤ 0.086.

**Impact on recorded results.** The p-values of every position_boxed check widen; none was recorded when passing (F03).
- **Q2-001 beats-null.** Winner EV +0.2134. Always-long +0.2144 (Shrinkage #24). The bounded cost is 0.051 R at the 2 % stop: the gross−net gap on the survey cell is 0.307 − 0.256. So the coin-side null mean is about (0.214 + (−0.265 − 0.051))/2 ≈ −0.051 R.
  - At the winner's N (6,946) and σ between 2.22 R (the plan's) and 4.09 R (the hold-20 sibling's), with a design effect of 1–2, z ≈ 3.8–9.9.
  - So it passes under any correction (p ≤ 7e-5 against 0.01). Outcome unchanged.
- **Q-005** (null on floor and leave-one-out) may *additionally* be refused by beats-null. Outcome unchanged.
- **Survey readiness, multi-day cells:** see F08.

**Migration.** ADR-0048. `Measurement` gains two fields with defaults, and the Register format is unchanged. The survey index gains `null_n` per cell. Old survey results stay valid as records but are re-labelled "pre-ADR-0048" on the readiness page.

---

### OTL-F02 — the nulls ignore same-date dependence (P0)

**Problem [V].**
- `day_boxed._null_from` (`engine/day_boxed.py:331-338`) and `_baseline_from` (`:361-369`) draw boxes **independently** across the whole partition: `rng.integers(0, longs.size, size=(draws, n_trades))`.
- The winner's trades are not independent. A signal such as `down_run` fires on many names on the same date (a market sell-off). The registered ρ values say so: Q2-001 ρ = 0.187, Q2-002 0.219, Q3-001 0.427, Q-004 0.434, Q-005 0.557, all measured on definition (`*-queue.jsonl` `power_plan.rho`).
- `position_boxed` orders its blocks by `(t.entry_index, t.name)` (`:198`, `:217`). `entry_index` is a **per-name bar index**, not a calendar date. On a common-span slice where late listers start later, block neighbours are not calendar neighbours.

**Why it matters [V-probe].** Probe A2 uses the day_boxed engine: 10 names, 1,260 days, σ 2 %, martingale, `down_run(2)` intraday, single cell, zero cost, 200 seeds. With ρ = 0 the null is exact; with a common factor ρ = 0.5 it is badly oversized.

| common-factor ρ | false positives at α = 0.01 | at α = 0.05 |
|---|---|---|
| 0.0 | 0.010 | 0.050 |
| 0.5 | **0.090** | **0.200** |

ρ = 0.5 is typical of large-cap daily returns. The registered ρ values come from the signals' same-day net R and are lower, but the deff is 1 + (m−1)ρ with m names firing per date. For a 98-name universe after a sell-off, m is large.

**Fix.** One function in `occams/inference.py` (new; see F20):
```python
def dependent_null(pool: Sequence[Box], *, winner_dates: Sequence[int], n: int, draws: int, seed: int,
                   side_rule: Literal["coin", "matched", "long"], block: int | None = None) -> np.ndarray:
    """Date-cluster moving-block bootstrap. Group the pool's boxes by calendar date. Resample
    blocks of consecutive dates (block length: core.stats.optimal_block_length on the pool's
    per-date mean series, at least the hold length). On each sampled date draw k boxes, k taken
    from the empirical distribution of the winner's per-date counts, so a draw clusters as the
    winner clusters. Concatenate to n; return per-draw means. Side per side_rule."""
```
- Both engines' `measure()` call it for the null (`side_rule="coin"`) and the baseline (F04: `"matched"`).
- `position_boxed` sorts by `(t.day, t.name)`; `TradeRecord.day` is the calendar ordinal.
- Keep the old function as `independent_null` for the synthetic engine, where independence is true by construction, and say so in its docstring.
- **Cross-check:** compute a cluster-robust t as well. The SE comes from the winner's trades summed per entry date, plus a Newey–West correction across dates with lag = hold. Record it beside the bootstrap p. If the two disagree by more than 2× on p, refuse with "the null and the analytic bound disagree".

**Tests** — `tests/test_dependent_null.py`:
- `test_dependent_null_preserves_date_clusters` — **RED** (function absent). With a pool of two dates × 50 boxes and winner counts all equal to 10, every draw's indices come from at most ⌈n/10⌉ dates.
- `test_position_boxed_orders_blocks_by_calendar_day` — **RED.** Two names whose bar indices are offset by 100 days. The trade ordering fed to the bootstrap is non-decreasing in `day`.
- `@slow test_day_boxed_beats_null_size_under_common_factor` — **RED (0.200).** Probe A2 at ρ = 0.5: false-positive rate at 0.05 ≤ 0.086.
- `@slow test_day_boxed_beats_null_size_without_dependence` — GREEN today (0.050) and must stay GREEN. Probe A2 at ρ = 0: rate within [0.02, 0.086].
- `@slow test_position_boxed_beats_null_size_under_common_factor` — Probe A1 with ρ = 0.5: rate at 0.05 ≤ 0.086 (RED until F01 + F02).

**Impact on recorded results.** Conservative: the null widens. Q-003 recorded p = 0.983-class failures (Q-004 #15: p_null 0.983, null mean −0.034) and stays refused. For Q2-001, the z of 3.8–9.9 computed under F01 already assumed deff ≤ 2, so it still passes. Survey readiness: see F08.

**Migration.** ADR-0048. The survey index gains `null_method: "date_cluster_block"`.

---

### OTL-F03 — p without +1, and no evidence recorded when a check passes (P0)

**Problem [V].**
- `p = exceed / len(m.null_ev)` (`guards/beats_null.py:26-27`; `beats_always_long.py:30-31`; `survey/candidates.py:412`). A Monte Carlo p of 0 is reported as such: both readiness pages show "0.0000 vs 0.01" for all 20 rows (`docs/surveys/grid-001-seed20260912-readiness.md`).
- When a check **passes**, nothing about it is recorded. Q2-001's `HypothesisResolved` (P2 #19) carries `refusals: []`. Its beats-null p, null mean and spread, the winner's σ and SE, and the fifth-check numbers exist nowhere in the Register.
- This is why §4 has to *estimate* Q2-001's p.

**Fix.**
- `p = (1 + exceed) / (1 + B)` (Phipson & Smyth 2010) everywhere. `DRAWS_PER_ALPHA = 20` stays, so `1/(1+B)` is always ≤ α/20.
- New record `GuardEvidence(hypothesis_id, spec_hash, check, passed: bool, evidence: dict)`, one per check, appended before `HypothesisResolved` for **every** check, pass or fail. `RefusalRecorded` stays for failures, for back-compatibility of readers.
- The evidence dict always includes `n`, `winner_ev`, `winner_sd`, `se_cluster`, `p`, `null_mean`, `null_sd`, `null_n`, `draws` and `method`.

**Tests:**
- `tests/test_guards.py::test_mc_p_value_is_never_zero` — **RED.** A null entirely below the winner gives `p == 1/(B+1)`.
- `tests/test_loop.py::test_resolution_records_evidence_for_passing_checks` — **RED.** Running the signal control through the loop yields five `GuardEvidence` records with `passed=True` and a numeric `p` on the two Monte Carlo checks.
- `tests/test_survey_page.py::test_readiness_prints_no_zero_p` — **RED.** The readiness document contains no "0.0000 vs".

**Impact.** Readiness pages print ≥ 0.00025 (1/4001) instead of 0.0000. No outcome changes: with B ≥ 2,000 the floor of p is ≤ 0.0005 < 0.01.

**Migration.** ADR-0048. `GuardEvidence` is a new `@register_record`. Its field names pass the S7 money check (`register/store.py:28-51`).

---

### OTL-F04 — the fifth check is side-blind and dependence-blind (P0)

**Problem [V].**
- `beats_always_long.check` compares the winner's EV with draws of always-long means: `exceed = sum(1 for x in base if x >= w.ev)` (`guards/beats_always_long.py:30`).
- The baseline is **always long** whatever the winner's side mix. It is drawn independently (day_boxed `:361-369`) or at the wrong N (F01).
- On the day-boxed null control, a **coin flip passes the fifth check** [V-probe, `make null` output and Probe A3]:

```
make null --engine=day_boxed → checks that passed: ['plateau', 'leave_one_out', 'beats_always_long']
winner stop 4 target 3: n 6295, EV −0.0797; always-long at this geometry −0.1033; margin +0.0236
baseline draws: mean −0.1031, sd 0.0090  →  z ≈ 2.6 → p ≈ 0.005 < α/9 = 0.0056
```

- The realised synthetic paths drifted down, so anything that is sometimes short beats always-long. The check attests "the side", which ADR-0043 says it must not.

**Design note.** The coordinator's phrase "paired on shared boxes" is right for one half and wrong for the other.

- **Execution component.** Fully pairing each trade with the passive trade on the same box is **degenerate for market entries**. Q2-001 is `down_run · market` (survey draft `f2199b5b297d85bb`). Its trade on box *b* **is** the always-long trade on box *b*, so the paired difference is identically 0.
- **Selection component.** The question the fifth check asks is whether the entry's *selection of boxes* (and its execution) beats passive exposure. Decompose:
  - margin = **selection** + **execution**
  - selection = mean over S of the passive outcome − mean over All of the passive outcome
  - execution = mean over S of (strategy − passive) on the same boxes
  - Here S is the set of boxes the winner traded, All is every gated box, and "passive" is side-matched.
- Pair the execution term: it has low variance and is exact for market entries (0).
- Test the selection term by randomisation: a random subset of size N from All, with the winner's date clustering, which is F02's `dependent_null` with `side_rule="matched"`.

**Fix.**
- `baseline = dependent_null(passive_pool, winner_dates=..., n=winner.n, side_rule="matched")`.
  - "matched": each drawn box takes the side of a randomly drawn winner trade, so the side mix is preserved.
  - For a long-only entry this equals always-long. For a coin flip it equals the coin null, and the check refuses.
- Statistic: `T = winner.ev − mean(passive over All, side-matched)`. Reject if `p = (1 + #{T*_b ≥ T})/(1 + B) ≤ α_c`.
- Record `selection` and `execution` separately in `GuardEvidence`.
- The ranking surface keeps ADR-0045's margin definition (now side-matched). The guard and the surface use the same number.

**Tests** — `tests/test_beats_always_long.py`:
- `test_fifth_check_refuses_coin_flip_on_drifting_paths` — **RED.** Runs the day-boxed null control's measurement (`controls._day_boxed_measurement("null", …)`) and asserts that `beats_always_long.check` returns a Refusal. Today it returns `None`.
- `test_market_entry_execution_component_is_zero` — **RED** (decomposition absent). For a `market` long entry, `evidence["execution"] == 0.0` exactly and `selection == margin`.
- `test_matched_side_equals_always_long_for_long_only` — GREEN guard rail. On a long-only fixture the matched baseline's draws equal always-long's at the same seed.
- `@slow test_fifth_check_size_on_martingale_world` — **RED (0.135 at 0.05; Probe A1).** False-positive rate ≤ 0.086 at 0.05 over 200 seeds.
- `@slow test_fifth_check_power_on_planted_reversal` — the signal control's `_reverting_walk` at planted 0.0100 is accepted in ≥ 0.65 of 50 seeds. This is the planned-power rate less Monte Carlo tolerance. If F05 changes the planted size, use the declared alternative.

**Impact.**
- **Q2-001**: margin −0.0010 (Shrinkage #24); p ≈ 0.5 under any null. **A re-score refuses it on the fifth check — certain.** The fifth check was not in force when it resolved (ADR-0043, "from the next registration"), so this is a G3 diagnostic and the outcome stays "supported".
- **Q2-002**: measured margin +0.075. It passed; under F01 + F02 its p rises. With σ about 2.2 R at hold 5 [I] and N 12,732, SE_iid ≈ 0.02 and z ≈ 3.8 iid, or ≈ 2.7 at deff 2 (p ≈ 0.0035 < 0.01). It probably still passes. Its outcome is null on the floor either way.
- **Control S3 (day_boxed null)**: the fifth check moves from "passed" to "refused". The control still refuses, now by three checks.
- **Programme 1**: no fifth check was in force; no re-score needed.

**Migration.** ADR-0049 amends ADR-0043 (the baseline is side-matched) and ADR-0045 (the margin is side-matched). The `Cell.baseline_ev` semantics change, so add `Cell.baseline_rule: str = "always_long"` so that old measurements read correctly.

---

### OTL-F05 — the floor is judged on the winner's point estimate (P0)

**Problem [V].**
```python
# guards/clears_floor.py:14
if w.ev < floor.ev_net_r:
```
- The floor is cleared by the point EV of the cell that **won** a k-cell sweep. A true effect sitting exactly at the floor passes about half the time.
- The maximum over k cells is biased upward (winner's curse).
- The power plan (`hypothesis.py:70-75`) sizes N to detect `floor/σ` against **zero**, two-sided: `n_for_mean_shift(floor.ev_net_r / self.sigma_r, alpha=self.alpha / search_space_size, …)`. Nothing is sized to show EV **above** the floor.

**Why it matters.** Bonferroni-simultaneous lower confidence bounds at α/k cover all k cells' means jointly with probability ≥ 1−α. Requiring `LCB_{α/k}(winner) ≥ floor` is therefore valid **after** selection, and it removes the winner's curse without a separate correction. Here k = `search_space_size`, matching `plan.alpha/k` in the other guards.

**Fix.**
```python
def check(m, floor, plan, search_space_size) -> Refusal | None:
    w = m.winner
    a_c = plan.alpha / search_space_size
    se = se_cluster(w.trades, by="day", hac_lag=hold_of(w))          # occams/inference.py
    lcb = w.ev - z(1 - a_c) * se                                     # one-sided
    if lcb < floor.ev_net_r: refuse("floor: the lower confidence bound on EV is below the declared floor (ADR-0050)", ...)
    ...frequency half unchanged...
```
- **Power.** Add a required per-question key `power.alternative_ev_net_r`: the EV the author wants the lab to have power **at**. It must be strictly greater than `floor.ev_net_r`. It has no default and is printed by `--schema`, as with R9.
  - `required_n = ceil(((z(1−α_c) + z(power)) · σ / (alternative − floor))²)`, one-sided, consistent with the LCB.
  - Record `alternative_ev_net_r` on `HypothesisRegistered` (new field, default 0.0 for old records, which means "pre-ADR-0050").
- **Scale** at α_c = 0.01, power 0.8 [V, computed]:

| σ (R) | alternative − floor = 0.05 | alternative − floor = 0.10 |
|---|---|---|
| 1.20 (programme 1) | 5,781 | 1,446 |
| 1.43 (Q3-001) | 8,254 | 2,064 |
| 2.22 (Q2-001 plan) | 19,801 | 4,951 |
| 4.09 (hold-20 sibling) | 67,308 | 16,827 |

  This is the honest cost of "clears the floor". Expect far fewer questions to be affordable. The readiness tables' "lowest affordable floor" column must be recomputed under the new formula.
- **Controls.** `controls.toml [signal] planted_ev_net_r = 0.165` sits just above the floor. Under the LCB rule S10 must plant at the declared alternative. Add `[power] alternative_ev_net_r` to `controls.toml` (apparatus numbers, not the author's). S10 then means "a planted effect at the alternative is accepted at planned power", measured over seeds by F23.

**Tests:**
- `tests/test_guards.py::test_floor_refuses_when_lcb_below_floor` — **RED.** A fixture with winner EV 0.16, n 1,000, sd 1.2, floor 0.15, α_c 0.01 gives LCB ≈ 0.072. Today it passes because 0.16 ≥ 0.15.
- `tests/test_guards.py::test_floor_lcb_widens_under_date_clustering` — two fixtures with identical trade values. One spreads trades over 1,000 dates, the other packs them into 100 dates of 10. The second's SE is ≥ 2× the first's, and only the first clears.
- `tests/test_hypothesis.py::test_required_n_targets_the_alternative` — **RED.** σ 1.2, floor 0.15, alternative 0.25, α_c 0.01 gives 1,446.
- `tests/test_config.py::test_alternative_has_no_default` — **RED.** A config without `alternative_ev_net_r` is refused, naming the key and no value.
- `@slow tests/test_controls.py::test_lcb_floor_coverage` — on 200 synthetic worlds with the true EV exactly at the floor, the floor check refuses in ≥ 1 − α_c − tolerance of seeds.

**Impact [V numbers, I σ].** Using the recorded EV and N and the plan σ:

| question | EV | N | σ used | LCB at 0.99, iid | at deff 1.5 | at deff 2 | floor 0.15 |
|---|---|---|---|---|---|---|---|
| Q2-001 | +0.2134 | 6,946 | 2.22 (plan) | **+0.151** | +0.138 | +0.126 | knife-edge → refuse |
| Q2-001 | +0.2134 | 6,946 | 4.09 (hold-20 sibling) | **+0.099** | +0.073 | +0.052 | refuse |
| Q2-002 | +0.109 | 12,732 | 2.2–4.09 | ≤ +0.07 | — | — | refuse (already) |
| Q-005 | +0.051 | 893 | 1.2 | −0.042 | — | — | refuse (already) |

- Q2-001 clears the floor at the 0.99 bound only if its effective N ≥ 6,640 at σ 2.22.
- Its own registered `available_n` was 6,286, which is the definition-derived effective N after ρ. On that number the LCB is **below** the floor.
- **A re-score under ADR-0050 refuses Q2-001's floor with high probability.**

**Migration.** ADR-0050. `HypothesisRegistered.alternative_ev_net_r` is a new field with a default. `whatif` and `power` call sites change, while the vendored `core/power.py` stays byte-identical: the one-sided formula lives in `occams/inference.py` or `hypothesis.py`. The quickstart's step 4 ("714") stays as the M0.15 known answer, labelled pre-ADR-0050.

---

### OTL-F06 — power is promised at the template's σ, not the winning cell's (P0)

**Problem [V].**
- Registration from a survey takes σ from the **survey cell's** row: `s = sigma if sigma is not None else row.get("sigma_net")` (`survey/candidates.py:318`).
- At measurement the guard compares only the **winner's trade count** with that N: `if m.winner.n < need` (`guards/measure.py:25`). The winner may be any of the sweep's cells, with a different σ.
- **Q2-001**:
  - Sweep: hold {1, 3, 5, 10, 20} × stop {2, 3, 5}. Plan σ = 2.2209 R, from the hold-5 survey cell (`programme-2-queue.jsonl`). `required_n` = 2,561.
  - The winner is `winner_cell [4, 0]`, i.e. **hold 20, stop 2 %** (P2 #19; `PROGRAMME-2-CONCLUSION.md:93` "At hold 20").
  - The ungated hold-20 sibling, Q2-002's survey cell, has σ = 4.0947 R, for which `required_n` = **8,704 > 6,946 measured**.
  - Q2-001 is under-powered at its own winner if its σ exceeds **3.658 R** [V, computed].
- M13.9's `bound_by_thinnest_cell` (`candidates.py:294-309`) fixed the same defect for N, but not for σ.

**Fix.**
- Registration: `σ_plan = max(σ_cell for cell in sweep if not refused)` from the survey index ("bound by the widest cell"), with its provenance (the cell id).
- Measurement (`guards/measure.py`, after `:25`):
  - recompute `need_w = required_n(σ = sd(winner.trades), floor, alternative, α_c)`;
  - refuse "underpowered at the winning cell's own dispersion (ADR-0050)" if `winner.n_eff < need_w`, where `n_eff` uses the cluster-robust design effect from F05.
  - This peeks at the measurement partition, but it can **only refuse**: it is conservative and spends nothing extra.
- Record `winner_sd`, `need_w` and `n_eff` in `GuardEvidence`.

**Tests:**
- `tests/test_guards.py::test_measure_refuses_when_winner_sigma_exceeds_plan` — **RED.** Plan σ 1.0, `required_n` 1,000, winner of 1,100 trades with sd 2.0 gives a refusal.
- `tests/test_survey_candidates.py::test_registration_sigma_is_the_widest_cell` — **RED.** Two kin cells with σ 1.5 and 3.0 give `power_plan.sigma_r == 3.0`, with provenance naming the 3.0 cell.

**Impact.** **Q2-001: medium–high probability of a REGISTERED→MEASURED refusal on re-score** [I]. This holds if its hold-20 gated σ is above 3.66 R; the ungated sibling's 4.09 R suggests so. The private `PathsArchived` sha `2a87f507…` (P2 #18) holds the trades and settles it in one line. Q3-001 (already refused for N) stays refused. Q2-002 is unaffected (null on the floor).

**Migration.** ADR-0050. No Register format change beyond F03's evidence.

---

### OTL-F07 — plateau slack is absolute, and the winner sits in its own median (P0)

**Problem [V].**
```python
# guards/plateau.py:30-32
score = m.score(w)
med = median(m.score(c) for c in neigh if c.trades)      # neigh includes w (line 21)
if score - med > gates.plateau_slack:                     # 0.10 for every question (queue gates)
```
- The slack is 0.10 R for every question, in R, whatever the surface. On the margin surface, margins run about −0.1 to +0.4.
- The winner is in its own neighbourhood. With 4 cells it is one of the two middle values, which pulls the median toward it.

**Fix.**
- Exclude the winner from the median.
- Declare `gates.plateau_slack_se` (in standard errors of the winner's score) and refuse if `score − median(neighbours) > plateau_slack_se · se_cluster(winner)`.
- Keep `plateau_slack` (absolute) **as well**, and refuse if either is exceeded. The two together are conservative.

**Tests:**
- `test_plateau_excludes_winner_from_median` — **RED.** Neighbourhood scores [0.30 (winner), 0.22, 0.18, 0.05] with `plateau_slack` 0.10.
  - Today the median includes the winner: 0.20, so the gap is 0.10, which is not > 0.10, and it passes.
  - After the fix the median excludes the winner: 0.18, so the gap is 0.12 and it refuses.
- `test_plateau_slack_in_standard_errors` — **RED.** Winner SE 0.01, slack_se 2, gap 0.05 gives a refusal.

**Impact.** Numbers move. The cell EVs of the P2 sweeps are in the private `PathsArchived` files, not in the Register. Probability of flipping Q2-001's plateau: low–medium [I]. Q-004's plateau was refused for neighbourhood size and stays refused.

**Migration.** ADR-0051. `Gates.plateau_slack_se` is required for new registrations; it is absent on old ones and read as "pre-ADR-0051".

---

### OTL-F08 — the survey's fifth check is selection-blind; no validate step; the wording says "halves" (P0)

**Problem [V].**
- `fifth_check_readiness` (`survey/candidates.py:349-419`) tests the `TOP = 20` (`:42`) cells, which are the best by margin out of 38,976. It uses the **per-test** α of the axis: `alpha_c = float(cfg.alpha.axes[...].mechanism_test_alpha)` (`:399`), which is 0.01.
- Ranking on the margin and then testing the margin at an uncorrected α guarantees a pass for the top of the ranking. Both readiness pages read "20 of 20 candidates pass".
- The wording is wrong:
  - `README.md:128` "on the calibration half only"
  - `:134` "the half no one looked at"
  - `:178` and `:189` "calibration half"
  - The split is **0.3 / 0.5 / 0.2**, oldest first (`data/partitions.py:45-59`; every `CalendarFrozen` record).

**What the records say [V].** The two measured shrinkages fail in **different** ways. Selection-aware inference fixes only one of them.

| | definition EV → measured EV | always-long, definition → measured | margin, definition → measured |
|---|---|---|---|
| Q2-001 (#24) | 0.256 → 0.213 (−0.042) | 0.017 → **0.214** (+0.197) | 0.239 → −0.001 |
| Q2-002 (#35) | 0.333 → 0.109 (−0.224) | 0.132 → 0.034 (−0.098) | 0.201 → 0.075 |

- Q2-001's collapse is **baseline non-stationarity**: the market's 2003–2019 return at hold 20 in the up regime. That is F18's job.
- Q2-002's is mostly **winner's curse and EV decay**, which this fix addresses.

**Fix.**
1. **Max-statistic inference over the screen.** Use a Romano–Wolf step-down on studentised margins (preferred: it controls FWER and is less conservative than Bonferroni), or Hansen's SPA when only "is the best real?" is wanted.
   - Build the **cell × date** matrix of per-date margin contributions on the screening set.
   - Bootstrap dates in moving blocks (F02), with **one shared index draw for all cells**, so the cross-cell correlation is preserved.
   - Each cell's adjusted p replaces `p_baseline` in readiness. The threshold `[survey].fwer_alpha` is required and has no default.
   - Memory: about 2,500 definition dates × 38,976 cells ≈ 780 MB float64. Do it per family on a laptop, or whole on the burst instance (`tools/aws/burst.sh`).
2. **Screen / validate / measure.** Split the **definition** partition in time order: screen on eras 1–2 and validate on era 3.
   - `survey/run.py:220-225` `_eras` already cuts three eras.
   - A cell is "ready" only if its validate-era margin, tested **once per cell at the family-wise level of the top-K carried forward**, clears its threshold.
   - The measurement partition is untouched (D13), and the frozen calendars (ADR-0038) do not move.
3. **Shrinkage in the table.** Print an empirical-Bayes shrunk margin per cell: normal–normal, with the prior fitted on the screen's cell distribution. Print the shrinkage the recorded Q2 pairs imply (Δ −0.240, −0.127) as the realised prior.
4. **Wording.**
   - README: "on the definition partition — the oldest 30 % of the frozen calendar".
   - README: "on the measurement partition — the next 50 %, read once".
   - `docs/EXTENDING.md` and `docs/SETUP.md`: same.

**Tests** — `tests/test_survey_inference.py` (new):
- `test_readiness_on_a_null_grid_passes_nothing` — **RED.** A synthetic grid of 2,000 cells has a margin of exactly 0 in expectation (always-long-matched noise). Today's `fifth_check_readiness` passes ≥ 15 of the top 20; after the fix at most 1 of the top 20 passes at FWER 0.05.
- `@slow test_romano_wolf_controls_fwer_on_null_grid` — over 200 seeds of a 500-cell null grid with cross-cell correlation 0.5, the share of seeds with ≥ 1 false "ready" is ≤ 0.05 + 0.036.
- `@slow test_romano_wolf_power_on_planted_cells` — plant 5 of 500 cells at 4 SE: ≥ 4 of 5 found in ≥ 80 % of 100 seeds.
- `test_validate_era_is_inside_definition` — the validate slice's bounds lie within `CalendarFrozen.definition` and never touch `measurement_end_day`.
- `tests/test_docs.py::test_no_halves` — **RED.** `README.md` contains neither "calibration half" nor "half no one looked at".

**Impact.** Readiness tables only; no verdict.
- **grid-001 and grid-002**: "20/20 pass" will not survive as such [I, medium–high].
  - The sp_100 and dow_30 cells have N in the thousands and margins of 0.18–0.24. At σ 2.2 R, SE_iid ≈ 0.036, so z ≈ 5–6.5.
  - That exceeds the Bonferroni bar over 38,976 cells (z = 4.70 one-sided at 0.05), so **some survive Romano–Wolf if dependence is mild**.
  - Under date-clustering with m ≈ 10 names per sell-off date and ρ ≈ 0.17, deff ≈ 2.5, z ≈ 3.2–4.1, so **most fall**.
  - index_etfs and sector_etfs cells (4–11 names, smaller N) fall [I]. The per-cell N is in the private survey index.
- Note honestly: **this fix alone would probably not have stopped Q2-001** (its definition z is large). F18 would have flagged it.

**Migration.** ADR-0052 amends M12.3/M12.4. `SurveyRecorded` gains `inference: "romano_wolf"` and `fwer_alpha`. Old readiness pages stay as committed and are labelled "pre-ADR-0052".

---

### OTL-F09 — the overlap gate is bypassed by any free-text distinction, and by a change of axis (P1)

**Problem [V].**
```python
# ledger/alpha_budget.py:225  overlap(): different axis → 0.0
if new.axis is not old.axis or new.partition != old.partition:
    return 0.0
# :253  gate(): any non-empty text passes
if supersedes == old.hypothesis_id or (distinction or "").strip():
    continue
```
- Survey registration fills the distinction automatically with the mechanism sentence (`survey/candidates.py:343`), so the gate never refuses a survey question.
- **Q2-002** (axis `price_daily`) re-measured Q2-001's mechanism (axis `regime`): same `down_run(4)·market`, same sweep, same 98 names, same measurement bounds 731258–737410 (P2 #14, #27). It registered two days after Q2-001's always-long number on that partition was known (#24 at 2026-09-17; #26 at 2026-09-19).
- The outcome was null, so no harm was done, but the rule allowed a second look.

**Fix.**
- **Structural overlap key:** `(universe members, partition bounds, entry kind, entry side)`, regardless of axis or regime gate. The overlap fraction is computed on (name, day) as now.
- Above `overlap_threshold` the registration needs `supersedes=<resolved id>`. A **structural distinction** is a typed value checked by code, not prose:
  ```
  Distinction(kind="disjoint_params" | "different_entry_kind" | "disjoint_names" | "disjoint_days", detail=…)
  ```
- A superseding question on overlapping data spends from a **data-set budget**: new required key `[lab].per_dataset_alpha`, applied per (universe, partition). Repeated looks at one measurement partition share one budget.
- `candidates.py:343` stops writing the mechanism sentence into `distinction`; the sentence moves to `mechanism`, where it already is.

**Tests** — `tests/test_ledger.py`:
- `test_overlap_is_axis_agnostic` — **RED.** Q2-001 and Q2-002 fixture shapes (axes regime vs price_daily, same names and days) give an overlap of 1.0.
- `test_free_text_distinction_no_longer_bypasses` — **RED.**
- `test_structural_distinction_admits_disjoint_params` — the same entry kind with disjoint `runs` sets is admitted.
- `test_dataset_budget_shared_across_superseding_questions` — two registrations on one partition cannot together exceed `per_dataset_alpha`.
- `tests/test_survey_candidates.py::test_survey_registration_does_not_autofill_distinction` — **RED.**

**Impact.** None on recorded verdicts (prospective). Recorded diagnostic: Q2-002 would have needed `supersedes: Q2-001` and been charged against the sp_100 measurement-partition budget.

**Migration.** ADR-0053. `HypothesisRegistered.distinction` becomes a typed dict. Old records hold a string, which readers treat as `kind="legacy_text"`.

---

### OTL-F10 — accrual outside the declared total; no lab-wide alpha ceiling (P1)

**Problem [V].**
- The invariant explicitly excludes accruals: "Accruals are new budget against new observations and sit outside the declared total by design" (`ledger/alpha_budget.py:135-138`).
- `accrue()` grows an axis without bound (`:195-205`).
- Each programme declares its own total in its own git-ignored config. The lab declared **1.20** across three programmes and spent 0.55 (`docs/LAB-CONCLUSION.md:27`).
- A union bound across the lab is therefore up to 1.2: a family-wise statement at no conventional level.
- Each question was charged 0.15 (P2 #12, #25; P3 #10), so each "supported" carries a question-level family-wise error of up to 15 %.

**Fix.**
- Add a required key `[lab].alpha_ceiling` and a **lab ledger** that replays **every** programme Register named in `[lab].registers`. The console already reads all three.
- Registration refuses if lab-wide spent + requested > ceiling.
- Accrual is allowed only inside the ceiling. Alternatively, adopt **alpha-investing** (Foster & Stine 2008), where wealth grows only by rejections, as a declared choice in `[lab].error_control = "ceiling" | "alpha_investing"`.
- Recommend `"ceiling"`: it matches the lab's FWER posture. Mention LORD++ only as an FDR option for an explicitly exploratory tier.
- The console prints a "question-level family-wise error" line beside each verdict: `alpha_spent` = 0.15 for Q2-001.

**Tests** — `tests/test_ledger.py`:
- `test_accrual_cannot_exceed_lab_ceiling` — **RED.**
- `test_ceiling_spans_programme_registers` — **RED.** Three tmp Registers with spends 0.10, 0.30 and 0.15 against a ceiling of 0.50 refuse the next 0.04.
- `test_invariant_counts_accruals_against_ceiling` — **RED.**
- `tests/test_config.py::test_alpha_ceiling_has_no_default` — **RED.**

**Impact.** No verdict changes. The console shows lab-level spent/ceiling.

**Migration.** ADR-0053. Add `LabCeilingDeclared(ceiling, registers, decided_by)` as the first record of a new `register/lab.jsonl`, or of `diagnostics.jsonl` if you prefer a single side store.

---

### OTL-F11 — the Register is keyless: forgery and truncation verify; heads pinned nowhere (P1)

**Problem [V, V-probe].** The digest is `sha256(prev|seq|canonical(payload))` with no key (`register/store.py:103-104`). Probe A4:
- Flipping Q2-002's `outcome` to `"supported"` and recomputing the chain gives `Store("forged.jsonl").verify() == 37`.
- Truncating `programme-2.jsonl` to 20 lines gives `verify() == 20`.

The heads (`c2706a09716b`, `23cf22aa6586`, `e92fda14a7f1`) appear only in prose (`docs/LAB-CONCLUSION.md:6-8`, the HTML pages, and TASKS). No test reads them. The public history is a single snapshot (17 commits, all 2026-10-03), so git cannot show registration before measurement. The `at` timestamps are self-reported.

**Fix.**
1. **Pinned heads.** `register/HEADS.toml`, one table per store: `path`, `count`, `head_sha`, `pinned_at`.
   - `tools/prepublish.py` and a new test fail on any mismatch.
   - Appending updates HEADS through `occams register pin`. The loop does it after its last append.
2. **Signed heads, third-party verifiable, no new Python dependency.**
   - `ssh-keygen -Y sign -f <the author's key file> -n occams-register register/HEADS.toml` *(reworded for publication: the original names a path under the home directory)* produces `HEADS.toml.sig`.
   - Commit `register/allowed_signers`.
   - Verify with `ssh-keygen -Y verify -f register/allowed_signers -I author -n occams-register -s register/HEADS.toml.sig < register/HEADS.toml`. GitHub runners have OpenSSH.
   - Also push a signed tag `register/<store>/<count>` per pin.
3. **External anchor.** `ots stamp register/HEADS.toml` (OpenTimestamps, optional tool). Commit the `.ots` proof, then `ots upgrade` later.
   - This dates the heads independently of GitHub and of the author's clock.
   - When the tool is absent, `make anchor` refuses loudly; it never skips silently.
4. **Keyed MAC (optional, private).** `mac = HMAC-SHA256(OCCAMS_REGISTER_KEY, sha)` beside `sha` on each line. It proves integrity to the key holder only, so it ranks below 2 and 3.
5. **Backfill.** Pin today's six heads as they verify now. The anchor dates the *pin*, not the past. Say so in ADR-0054: the pre-pin history is attested by the private repository and the dated pages, not by this mechanism.

**Tests** — `tests/test_register_anchor.py`:
- `test_committed_registers_match_pinned_heads` — **RED** (no HEADS file).
- `test_forged_and_rechained_register_fails_against_pin` — **RED.** Probe A4's forgery as a test.
- `test_truncated_register_fails_against_pinned_count` — **RED.**
- `test_heads_signature_verifies` — skipped with a loud reason **only** if `ssh-keygen` is missing; required in CI.
- `tests/test_prepublish.py::test_prepublish_checks_heads` — **RED.**

**Impact.** None on numbers. It closes the gap between "append-only" (true in code) and "cannot be rewritten undetectably" (false today).

**Migration.** ADR-0054. The line format is unchanged. HEADS, the signature, `allowed_signers` and the `.ots` proof are side files. CI adds a "verify signed heads" step.

---

### OTL-F12 — append is unlocked and quadratic (P1)

**Problem [V].**
- `append()` (`register/store.py:117-126`) calls `verify()`, which reads and parses the whole file, then `_lines()` (a second full read), then opens in append mode. There is no lock.
- Two appenders that both read `n` both write `seq n`, forking the chain.
- `records()` (`:128-130`) re-verifies on every call. `falsifier.standing` calls `register.records()` three times (`falsifier.py:23-38`), and the ledger replays it again, so the cost is O(records²) across a loop.

**Fix.**
- `fcntl.flock(LOCK_EX)` on `<path>.lock` around read-tail, verify-tail, write and `fsync`.
- Cache `(st_ino, st_size, st_mtime_ns, n, head)` after a full verify, and verify only the appended tail when the prefix size is unchanged.
- On a size **decrease**, raise `TamperedHistory("truncated")`. That catches truncation within a session; F11 catches it across sessions.

**Tests:**
- `test_concurrent_appends_never_fork_chain` — **RED** (deterministic). Monkeypatch a hook between read-tail and write that lets a second process append. After both finish, `verify()` passes and the seqs are unique. Today it raises `TamperedHistory` or duplicates a seq.
- `test_append_reads_file_at_most_once_after_warm_cache` — **RED.** Count `Path.read_text` calls: ≤ 1 per append once warm.
- `test_shrinking_file_raises_truncated` — **RED.**

**Impact.** None. **Migration.** None (behavioural).

---

### OTL-F13 — engine identity: `-dirty` and `unknown` accepted; the content hash covers a hand list (P1)

**Problem [V].**
- `engine_sha()` returns `HEAD + "-dirty"` if `git status --porcelain` shows **anything**, and `"unknown"` on any exception (`core/archive.py:97-106`).
- Every programme 2 verdict-path record is `-dirty` (P2 #15, #19, #28, #33), as are both `SurveyRecorded` (P2 #9, P3 #9). `compile.py:136-142` blames the loop's own Register writes and says "`engine_code_sha` (the content hash on every record) stays the reproduction key".
- But no `HypothesisMeasured` or `HypothesisResolved` in any Register carries `engine_code_sha`. Only P3's `SurveyRecorded.engine_shas` does.
- `engine_code_sha()` (`survey/run.py:47-59`) hashes a **hand-maintained list** of 11 files. It omits:
  - `occams/core/execution.py` (every fill)
  - `occams/sizing.py` (`r_multiple`)
  - `occams/measurement.py` (winner and score)
  - `occams/guards/*`
  - `occams/data/partitions.py`
  - `occams/engine/synthetic.py`

**Fix.**
- `occams/identity.py`:
  - `code_closure_sha(entry: Iterable[str]) -> str` is the sha256 over the transitive **import closure inside `occams/`** of the given modules. It uses the AST walk `tools/closure.py` already has, with files sorted and bytes hashed.
  - The entry set is `{"occams.loop", "occams.engine.day_boxed", "occams.engine.position_boxed", "occams.survey.run"}`.
- `engine_sha` (wrapper, not the vendored function) checks dirtiness with `git status --porcelain -- occams tools pyproject.toml`, so outputs (`register/`, `archive/`, `docs/`, `build/`) cannot dirty it.
- Stamp `engine_code_sha` on `HypothesisMeasured`, `HypothesisResolved`, `SurveyRecorded` and `Rescored` (new field, default "").
- Refuse at REGISTERED→MEASURED and at survey start if the code is dirty or the commit is `"unknown"`: `EngineNotClean` (ADR-0055). The apparatus controls are exempt; they stamp and say so.

**Tests:**
- `test_code_closure_sha_covers_fills` — **RED.** Copy the tree to tmp, change one byte of `occams/core/execution.py`, and the sha changes. Today `engine_code_sha()` is unchanged.
- `test_register_append_does_not_dirty_engine` — **RED.** In a tmp git repo, appending to `register/x.jsonl` leaves `engine_sha()` clean.
- `test_measure_refuses_dirty_code` — **RED.**
- `test_measure_refuses_unknown_commit` — **RED.**

**Impact.** None on numbers. Future records become reproducible by content.

**Migration.** ADR-0055. The vendored `core/archive.py` stays byte-identical and the lab stops calling its `engine_sha` directly. `test_provenance` is untouched.

---

### OTL-F14 — the stamped commits are missing from the public history (P1)

**Problem [V].** See G4. The five verdict commits are not reachable from the public repository (`git cat-file -e` fails). `reproduce private --at-commit` (`reproduce.py:175-188`) cannot run for anyone but the author, in a different repository. `docs/PUBLICATION.md`'s amendment of 2026-10-03 records the decision that the public repository carries no history.

**Fix.** Keep the decision, and make the sources addressable without the history:
- `SOURCES.toml` (committed, signed with F11's key) maps each stamped `engine_sha` to its `tree` hash, its `engine_code_sha` (computed retroactively in the private repository) and the archive path of a **source snapshot** `archive/source/<engine_code_sha>.tar.zst` beside the bars.
- `reproduce private --at-source <engine_code_sha>` extracts the snapshot to a tmp dir, in place of `git worktree add`.
- Optionally publish the snapshots of the six verdict trees as release assets. They are code, not licensed bars, so prepublish still applies.

**Tests:**
- `test_every_resolved_names_a_known_source` — **RED.** Every `HypothesisResolved.engine_sha` (minus `-dirty`) in the committed Registers is a key of `SOURCES.toml`.
- `test_reproduce_at_source_refuses_missing_snapshot_loudly` — prints "REPRODUCTION FAILED … no snapshot …", rc 2.

**Impact.** None. **Migration.** ADR-0055.

---

### OTL-F15 — survivorship: current members measured on 1993–2019 (P2)

**Problem [V].**
- `sp_100` and `dow_30` are "as listed on 2026-09-12". The bias is **named** on the record ("survivorship by construction …", P2 #4, #11; `PROGRAMME-2-CONCLUSION.md:51`) but **not corrected**.
- ADR-0025's title says "The universe is a point-in-time rule".
- The measurement partition is 2003-02-12 → 2019-12-17. Always-long at hold 20 in the up regime earned +0.214 R there (P2 #24), which is partly the return of the names that survived.
- A reversal after a down-run on survivors is the textbook case: names that kept falling were removed from the index, and they are not in the sample.

**Fix.**
- `UniverseDeclared.rule_kind = "point_in_time"` with membership intervals `{name: [(from_day, to_day), …]}`, a provenance and rights record (M12.1b/c pattern).
- The engines admit a box only if `name ∈ members(day)`. Delisted names exit on their terms through the existing `actions.delisting` path (`day_boxed.py:256-258`).
- If PIT data is unobtainable at the data budget (ADR-0028), the universe must carry a **measured survivorship diagnostic** before any question on it can register:
  1. re-measure on `members as of the measurement start date` (the 2003 list) where bars exist;
  2. re-measure on the ETF universes, where there is no single-name survivorship;
  3. record the differences as `SurvivorshipDiagnostic`.

**Tests:**
- `test_box_admitted_only_inside_membership` — **RED.**
- `test_current_list_refused_for_historical_partition_without_diagnostic` — **RED.** Registering on a `rule_kind="current"` universe whose measurement partition predates `chosen_on` is refused unless a `SurvivorshipDiagnostic` exists.
- `test_delisted_name_trades_until_delisting` — GREEN regression on the existing path.

**Impact (non-conservative).**
- **Q2-001: verdict at risk in either direction** [I]. Both its EV and the always-long baseline fall: survivors inflate both. The floor (absolute) becomes harder; the margin's sign is ambiguous.
- **Q2-002**: EV likely falls further, so it stays null.
- Q-003, Q-004, Q-005 and Q3-001 are on ETFs and are unaffected.

**Migration.** ADR-0056 amends ADR-0025. New record kinds `UniverseMembership` and `SurvivorshipDiagnostic`.

---

### OTL-F16 — costs are a declared bound never measured; stops fill at the level (P2)

**Problem [V].**
- `DECLARED_SPREAD[US_LARGE] = (0.0002, 0.0010)` is "declared range; M5.0 measurement on the demo account pending" (`costs/equity.py:53-58`). M5.0 was closed by decision and the cost basis stays `bounded`.
- Every verdict was taken at 10 bp round trip: `cost_in_r = c/s`, so 0.05 R at a 2 % stop. The survey cell confirms it: gross 0.307 − net 0.256 = 0.051.
- Stops fill exactly at the level unless the bar gaps (`day_boxed.py:250`; `position_boxed.py:107`). There is no slippage on a stop-market fill.

**Fix.**
- **Measured spread**: per instrument class, from venue quotes with provenance (`basis="measured"`), sampled at the hours the strategies trade.
- **Stop slippage**: required `costs.stop_slippage_fraction_of_atr`, applied to `"stopped"` exits.
- **Cost curve**: each resolution records EV at {measured, bound, 2 × bound} as diagnostics, not gates.

**Tests:**
- `test_stopped_exit_pays_declared_slippage` — **RED.**
- `test_resolution_records_cost_curve` — **RED.**
- `test_measured_basis_requires_provenance` — refuses observations without provenance.

**Impact (non-conservative, [V] numbers).**
- **Q2-002** (winner `[2, 0]` = hold 5, stop 2 %, EV 0.1089) needs +0.0411 R to reach the floor. That requires a measured round-trip cost ≤ **1.8 bp**.
  - Plausible on-exchange for S&P 100 names; unlikely at a retail venue of the leveraged-product kind [I]. *(Reworded for publication: the original names two venue types that are on this repository's R6 list.)*
  - **It could flip only a point-estimate floor.** Under F05 its LCB is at most about +0.07, so it cannot. Land F05 first (G5).
- **Q-005** (hold 5, stop 3 %) can gain at most 0.033 R, giving EV 0.084 < 0.15. No.
- **Q-003 and Q-004** (stop 3 %, EV −0.047 and −0.045) can gain at most 0.033 R. No.
- **Q2-001** gains up to 0.035 R from costs and loses from stop slippage. Net direction is unknown [I].

**Migration.** ADR-0057 amends D23 and reopens M5.0 as "measured, or swept with the curve recorded".

---

### OTL-F17 — wire the vendored calibration gate (P2)

**Problem [V].** `occams/core/calibration.py` (308 LOC) is imported by nothing in the lab (`grep occams.core` outside `core/`). Its contract, an estimator returns about 0 on a world with no effect and recovers a planted one, is exactly what F01, F02 and F04 violated without any test noticing.

**Fix.**
- `occams/calibrate.py` runs, per engine and per `engine_code_sha`, the guard set on the F23 size and power worlds (martingale; common factor ρ; drifting always-long; planted reversal at the alternative).
- It records `ApparatusCalibrated(engine, engine_code_sha, sizes, powers, seeds)`.
- REGISTERED→MEASURED refuses if no `ApparatusCalibrated` record exists for the current `engine_code_sha`.
- Reuse `core/calibration.py` where its estimand fits; otherwise say in the ADR why it stays unused (F19).

**Tests:**
- `test_measure_refuses_without_calibration_for_this_code` — **RED.**
- `@slow test_calibration_record_matches_size_table` — the recorded sizes are within tolerance of F23's table.

**Impact.** None. **Migration.** ADR-0058. New record `ApparatusCalibrated` in `register/diagnostics.jsonl`, or in the programme Register for new programmes.

---

### OTL-F18 — baseline non-stationarity: the definition partition is the oldest 30 % (P2)

**Problem [V].** The always-long return at a geometry is a property of the era (`PROGRAMME-2-CONCLUSION.md:93`). At hold 20 in the up regime it was +0.016 on 1993–2003 and +0.214 on 2003–2019. The readiness tables show "Always-long, survey → now" only **on definition**.

**Fix.**
- Readiness adds, per cell, the always-long return by definition era and a **baseline-instability statistic**: `max_era − min_era` in SEs. It also adds the margin against the **era-local** baseline.
- A cell whose baseline moves by more than `[survey].baseline_instability_se` (required) is not "ready".
- For **new** universes only, recommend calendars that interleave screen and measure by year-blocks. This is an ADR-level change; ADR-0006 and ADR-0038 stand for existing calendars.

**Tests:**
- `test_readiness_flags_unstable_baseline` — **RED.** Era baselines [0.0, 0.0, 0.2] with SE 0.03 are flagged.

**Impact.** Readiness only. Q2-001's survey cell had era margins +0.186 / +0.331 / +0.169 (readiness row 1). Its baseline instability inside definition is unknown from the committed page [I]. The 0.016 → 0.214 jump happened **across** the partition boundary, so this fix can only flag a trend that is already visible inside definition.

**Migration.** ADR-0052.

---

### OTL-F23 — controls show "refused once", not the guards' false-positive rate (P1)

**Problem [V].**
- `test_boundary_sensitivity_across_seeds` (`tests/test_controls.py:45-54`) runs 20 seeds and asserts the null is **never** accepted and the signal is accepted ≥ 50 %.
- The null world's mean is −`cost_in_r` = −0.05 (`controls.toml:19`) against a floor of 0.15, so the floor alone refuses it. Beats-null's and the fifth check's size are never measured, which is how F01, F02 and F04 survived.
- On the day-boxed null control the fifth check **passes** (F04).

**Fix.** Add a **size and power table** (`occams/calibrate.py`, `make calibrate`, nightly CI `schedule:` job running `-m slow`). Each guard is run **in isolation** on:

| world | purpose |
|---|---|
| martingale, zero cost, ρ ∈ {0, 0.5} | size of beats-null |
| drift so always-long > 0, long-only entry with no timing skill | size of the fifth check |
| true EV = floor | coverage of the LCB floor |
| planted at the alternative | power |

Assert, for S seeds, `size ≤ α + 2.33·sqrt(α(1−α)/S)` and `power ≥ planned − 2.33·sqrt(p(1−p)/S)`. S ≥ 200 for size, S ≥ 100 for power. Probes A1 to A3 are the starting point.

**Tests.** The `@slow` size and power tests listed under F01, F02, F04, F05 and F08 live in `tests/test_apparatus_size.py`. Also:
- `test_null_control_refuses_by_more_than_the_floor` — **RED.** Today the day-boxed null passes beats-always-long. Assert each of beats-null and beats-always-long refuses the null control in isolation.

**Impact.** None on records. Makes S3 and S10 meaningful.

**Migration.** ADR-0058. CI: the nightly job, and a weekly re-run of `make calibrate` on `main`.

---

### OTL-F19 — dead vendored modules; boto3 path reachable (P3)

**Problem [V].**
- The lab imports from the vendored core only `execution` (both engines), `power` (`hypothesis.py`, `proposers/clustering.py`, `survey/run.py`, `whatif.py`), `stats.optimal_block_length` (`position_boxed.py:183`) and `archive.engine_sha` (`compile.py`, `reproduce.py`, `engine/synthetic.py`).
- `calibration`, `estimators`, `experiment`, `result` and `backfill` (about 1,050 LOC) are reached by vendored tests only.
- `core/archive.py:61-66` imports boto3, which is not a declared dependency (`pyproject.toml`: `numpy>=1.26` only).

**Fix.** Keep the vendored core byte-identical: its provenance is a feature.
- Add `tests/test_core_usage.py`, pinning the set of vendored modules the lab imports. A change is a recorded decision.
- Add `test_check_never_imports_boto3`: after importing every lab module and running the controls, assert `"boto3" not in sys.modules`.
- Wire `calibration` (F17), or record in ADR-0058 that it stays unused, and why.

**Tests.** Both above; `test_core_usage` is **RED** until written, then GREEN.

**Impact.** None. **Migration.** None. `test_provenance` (12 modules) is unchanged.

---

### OTL-F20 — probes and the fifth check are duplicated (P3, but do it first in phase 2)

**Problem [V].** The always-long probe, the random-entry probe, null building and the fifth check exist in three places:
- `day_boxed.py:306-347,361-369`
- `position_boxed.py:188-225`
- `survey/candidates.py:360-413`, which re-implements α, `need` and p rather than calling `guards.beats_always_long`.

Every P0 fix would otherwise be made three times.

**Fix.**
- `occams/engine/probes.py`: `passive(compiled, bars, side_rule)` and `random_entry(compiled, bars, seed)`, engine-dispatched.
- `occams/inference.py`: `dependent_null`, `p_value`, `se_cluster`, `lcb`, `romano_wolf`.
- `guards/*` and `survey/candidates.py` call only these.
- `position_boxed` stops importing private helpers from `day_boxed` (`:27-28`: `_cost`, `_on_basis`). Move them to `occams/engine/common.py`.

**Tests:**
- `test_survey_and_guard_share_fifth_check` — **RED.** `survey.candidates.fifth_check_readiness` calls `occams.inference`'s function (identity check via monkeypatch spy).
- `test_engines_import_no_private_names_across_modules` — an AST check that no `from occams.engine.X import _name`.

**Impact.** None. **Migration.** None.

---

### OTL-F21 — entry kinds are an if/elif chain (P3)

**Problem [V].**
- `day_boxed.signal()` (`:123-170`) is the only signal implementation; `position_boxed` imports it (`:27-28`).
- `docs/EXTENDING.md` §3 lists five steps (ADR, enum, sentence, signal, auditor family), and only the family is enforced (`UnauditedFamily`).

**Fix.**
- `occams/entries/<kind>.py`, each with `KIND`, `PARAMS`, `SENTENCE`, `FAMILY`, `ADR`, and `fire(bars, first, actions, params) -> (bool, Side, level | None)`.
- `occams/entries/__init__.py: REGISTRY` is closed. `EntryKind` is checked against it at import.
- **Look-ahead property:** reuse `proposers/regime.py:125-139` `assert_causal`. Perturbing bars at or after `first` never changes `fire(..., first, ...)`.

**Tests:**
- `test_every_entry_kind_is_a_complete_module` — **RED** (registry absent): it checks sentence, family, ADR file present and params schema.
- `test_every_entry_kind_is_causal` (property, 20 trials per kind) — a look-ahead guard the lab does not have today for entries.

**Impact.** None. **Migration.** ADR-0059 amends ADR-0037. The kinds stay closed by decision.

---

### OTL-F22 — stale strings (P3)

**Problem [V].**
- `Makefile:48` "naming that all four checks passed"; the output says five (`tests/test_controls.py` asserts "all five checks passed").
- `controls.toml:18` "above the 834 the plan requires at 9 cells"; the computation gives **837** (`n_for_mean_shift(0.125, 0.05/9)`, and `make null` prints "required 837").
- `README.md:128,134,178,189` "halves" (F08).

**Fix.** Edit the strings.

**Tests** (`tests/test_docs.py`):
- `test_makefile_says_five_checks` — **RED.**
- `test_controls_comment_matches_computed_n` — **RED.** Parse the integer in the comment and compare it with `required_n`.
- `test_no_halves` — **RED.**

**Impact / Migration.** None.

---

### OTL-F24 — lint too narrow; small smells (P3)

**Problem [V].**
- `ruff` selects `E4, E7, E9, F` only. Under `E,F,B,SIM,C90`, `occams/` minus `core/` gives:
  - 2,229 E501
  - 25 C901 (`survey/grid.py:222 load` 37, `survey/candidates.py:577 register_main` 33, `survey/run.py:497 run_survey` 17)
  - 13 B905 `zip` without `strict`, including `guards/plateau.py:21` (index tuples of unequal length would be silently truncated)
  - 3 B008
  - 2 B023, at `proposers/regime.py:134`; benign, since the lambda is used immediately.
- Duplicate import: `ledger/alpha_budget.py:25` `from dataclasses import dataclass, replace` and `:32` `from dataclasses import dataclass as _dc`.
- `guards/leave_one_out.py:23-26`: when `pooled ≤ 0`, `loo_min_fraction * pooled` changes the check's meaning. It refuses in practice, but under a misleading message.
- `core/archive.py:106` returns `"unknown"` (F13).

**Fix.**
- `select = ["E", "F", "B", "SIM", "UP", "C90"]`, `line-length = 120`, `[tool.ruff.lint.mccabe] max-complexity = 15`, with per-file ignores for the three CLI mains and a ticket each.
- Use `zip(..., strict=True)` in guards and engines.
- `leave_one_out`: if `pooled ≤ 0`, refuse "the pooled score is not positive; leave-one-out has nothing to preserve".

**Tests:**
- `test_plateau_neighbourhood_rejects_mismatched_indices` — **RED** (strict zip).
- `test_loo_refuses_nonpositive_pooled_with_named_reason` — **RED.**

**Impact / Migration.** None.

---

### OTL-F25 — TASKS diary and CLAUDE.md size (P3)

**Problem [V].**
- `TASKS-v4.md` is 463 KB and 5,455 lines. Its `## Status log` starts at line 723, so about 4,730 lines (87 %) are diary.
- `CLAUDE.md` is 42 KB and 285 lines, its longest line 17,680 characters. It is a narrative, which an agent must load whole on every session.

**Fix.**
- `TASKS-v4.md` keeps lines 1–722 (plan, milestones, standing checks, definition of done). The status log moves to `docs/log/2026-09.md` and `docs/log/2026-10.md`, unchanged, with a one-line pointer.
- `CLAUDE.md` ≤ 5 KB:
  - state on date (3 lines)
  - standing rules (bullets)
  - where things are (table)
  - how a change is made (ADR, red test, `make check`)
  - pointers to `docs/log/`, `docs/INTEGRITY.md` and `docs/adr/`
  - no line over 200 characters

**Tests:**
- `tests/test_docs.py::test_claude_md_is_small` — **RED.** < 5,120 bytes, max line < 200.
- `test_tasks_has_no_status_log` — **RED.**

**Impact / Migration.** None. TASKS history stays in git and `docs/log/`.

---

## 4. Will these fixes change the lab's results?

**Principle.** The fixes in §3 split into two kinds:
- **Conservative** — they can only turn a pass into a refusal: F01, F02, F03, F05, F06, F08, F09, F10, F18, and the randomised (selection) half of F04.
- **Non-conservative** — they can move a number either way: F15 point-in-time universes, F16 measured costs (stop slippage alone is conservative), the paired execution half of F04, and F07's SE-based slack.

Therefore **every null verdict survives every conservative fix by construction**. What is at risk is the **one positive verdict (Q2-001)** and the **readiness tables**. Non-conservative fixes are applied after the conservative bundle (G5), so a null cannot be revived by a cheaper cost assumption on a guard set already known to be anti-conservative.

**Caveat.** None of this was re-run. The licensed archive, `occams.toml`/`configs/` and the `PathsArchived` trade files are private. Every number below is either read from the Register [V] or derived from it with the stated assumption [I]. The G4 procedure settles each one.

| Record | As reached | Fixes that touch it | Expected direction | P(outcome flips under a G3 re-score) | Reasoning |
|---|---|---|---|---|---|
| **Q-003** (P1 #9) | null: beats-null, floor, leave-one-out (2 groups) | F01–F05, F16 | stays null; more refusals | **≈ 0** | EV −0.047 on 1,391. LCB99 ≈ −0.12. Measured ETF spreads add at most +0.033 R at stop 3 %. Leave-one-out with 2 groups is structural. |
| **Q-004** (P1 #21) | null: all four | F02, F03, F05, F07, F16 | stays null | **≈ 0** | EV −0.045 on 2,088. Recorded p_null 0.983 (#15), null mean −0.034. Widening the null cannot help a winner below the null mean. |
| **Q-005** (P1 #32) | null: floor, leave-one-out (IWM; 0.014 without) | F01, F02 (position_boxed), F05, F16 | stays null; beats-null may also refuse | **≈ 0** | EV +0.051 on 893 with σ 1.2: LCB99 −0.04. Costs add at most +0.033 R, so EV 0.084 < 0.15. Leave-one-out unchanged. |
| **LabClosed** (P1 #33) | falsifier fired on 3 nulls | none | stands | **0** | It rests on three nulls that cannot flip. |
| **Q2-001** (P2 #19) | **supported** (four checks); margin −0.001 recorded | F04 (certain), F05, F06, F01/F02 (pass), F07, F15, F16 | toward refusal | **High (> 80 %) under the conservative bundle** | See below. |
| **Q2-002** (P2 #33) | null on the floor (0.109 < 0.15) | F01, F02, F04, F05, F15, F16 | stays null | **Very low with F05 in force; low without** | It needs +0.041 R. Measured costs supply it only if the round trip is ≤ 1.8 bp. Under F05 its LCB is ≤ about +0.07. Point-in-time membership likely lowers the EV. |
| **Q3-001** (P3 #12) | refused REGISTERED→MEASURED: 863 < 1,068 | F05 (alternative-based power), F06 | stays refused, by more | **≈ 0** | `required_n` rises with any alternative: σ 1.434 and alternative − floor 0.10 give 2,064. ETFs, so no point-in-time effect. |
| **grid-001 readiness** (2026-09-18) | 20 of 20 pass | F01 (multi-day rows), F02, F03, F08, F18 | toward fewer passes | **Medium–high that the table changes; low that it empties** | Large-N sp_100 and dow_30 cells have z ≈ 5–6.5 iid against the Bonferroni bar of 4.70, so some survive Romano–Wolf if dependence is mild. ETF cells and date-clustered single-name cells (deff ≈ 2.5) mostly fall. |
| **grid-002 readiness** (2026-09-20) | 20 of 20 pass | same | same | **Medium–high** | Same structure. Row 1 (dow_30, margin +0.371) is the likeliest survivor [I]. |
| **ProgrammeStopped** P2 #36, P3 #13 | author's stops | F10 (display only) | stand | **0** | The stops are author's acts. Balances are shown lab-wide only. |

**Q2-001 in detail.**
- *Beats-null (F01, F02): survives.* The coin-side null mean is about −0.051 R. At the winner's N and σ of 2.2–4.1 R, deff 1–2, z ≈ 3.8–9.9 and p ≤ 7e-5 against α_c 0.01.
- *Fifth check (F04): refused, certain.* Margin −0.0010 R on 6,946 trades gives p ≈ 0.5. It was not in force at the time (ADR-0043 binds forward), so it is recorded as a diagnostic.
- *Floor at LCB (F05): refused, high probability.*
  - At the plan's σ 2.22, LCB99 = 0.151 iid. It clears only if effective N ≥ 6,640.
  - The question's own registered `available_n` (after ρ) was 6,286, giving LCB ≈ 0.148. That is below 0.15.
  - At the hold-20 sibling's σ of 4.09, LCB99 ≈ 0.099.
- *Power at the winner's σ (F06): refused at REGISTERED→MEASURED, medium–high probability.* The winner is hold 20, stop 2 %. If its σ is above 3.66 R, `required_n` exceeds 6,946. Q2-002's ungated hold-20 cell has σ 4.09 R. The `PathsArchived` file `2a87f507…` settles it.
- *Point-in-time membership (F15): either direction.* Survivors inflate both its EV and always-long's.
- *Measured costs (F16): +0 to +0.035 R, minus stop slippage.* This is not enough to rescue the LCB under σ ≥ 2.2 with deff > 1.
- **Net:** a G3 re-score under ADR-0048 to ADR-0050 records "would not be supported". The verdict stays "supported" as reached, and the lab's own reading ("the entry added nothing", `LAB-CONCLUSION.md:52-59`) is reinforced, not overturned.

**What the lab's conclusion becomes.** "Four null, one supported whose entry added nothing, one refusal" becomes, with a diagnostic beside it: "four null; one supported under the rules then in force, refused under ADR-0049/0050 on re-score; one refusal".

The lab-level finding stands and is strengthened: **nothing found**. The guards were looser than claimed, and that looseness biases toward false positives. So the nulls are robust and the single positive was the soft spot.

---

## 5. Sequenced task list

Every task ends with an acceptance check. `make check` (`Makefile:39`) must pass at the end of every task unless the task says a named test is expected RED until a named later task.

### Phase 0 — governance, before any code (1 day)

| Task | What | Depends on | Acceptance |
|---|---|---|---|
| OTL-T01 | Write ADR-0047 (G1–G6). Reserve 0048–0060 in `docs/adr/README` or the ADR index. | — | ADR merged; `docs/adr/0047-*.md` exists. |
| OTL-T02 | Add `register/diagnostics.jsonl` store class (`Diagnostics(Store)`, record `Rescored`). Empty file committed. | T01 | `tests/test_register.py::test_diagnostics_store_accepts_only_rescored` GREEN. |
| OTL-T03 | F11 part 1: `register/HEADS.toml` pinning today's six heads (P1 34 `c2706a09716b…`, P2 37 `23cf22aa6586…`, P3 14 `e92fda14a7f1…`, plus the three queues), with the test and prepublish check. | — | `test_committed_registers_match_pinned_heads` GREEN; the forged-chain and truncation tests GREEN. |
| OTL-T04 | F11 part 2: SSH signing key, `allowed_signers`, `HEADS.toml.sig`, CI verify step; `ots stamp` (optional tool, loud refusal when absent). | T03 | CI "verify signed heads" green; `.ots` committed. |

### Phase 1 — make error rates measurable (2–3 days)

| Task | What | Depends on | Acceptance |
|---|---|---|---|
| OTL-T05 | F23: `occams/calibrate.py` and `tests/test_apparatus_size.py`, with Probes A1–A3 as `@slow` tests. **Expected RED**: A1 at 0.01, A1 at 0.05, A2 at ρ 0.5, A3 (fifth check on the null control). | T01 | Tests exist and fail with the probe numbers (±MC). The ρ = 0 control is GREEN. |
| OTL-T06 | F03: p + 1 and `GuardEvidence` for every check. | T05 | `test_mc_p_value_is_never_zero`, `test_resolution_records_evidence_for_passing_checks` GREEN. |
| OTL-T07 | F20: extract `occams/engine/probes.py`, `occams/engine/common.py`, `occams/inference.py` with **behaviour unchanged**. | T05 | All pre-existing tests GREEN; the probe numbers unchanged to the seed; `test_survey_and_guard_share_fifth_check` GREEN. |
| OTL-T08 | F13: `occams/identity.py`, closure sha, clean-code dirty check, `EngineNotClean`. | T07 | The four F13 tests GREEN. |

### Phase 2 — P0 inference fixes (1–2 weeks)

| Task | What | Depends on | Acceptance |
|---|---|---|---|
| OTL-T09 | ADR-0048. F01: winner-N resampling in position_boxed and the survey. | T07 | F01 unit tests GREEN; A1 at 0.01 GREEN (≤ 0.026); A1 at 0.05 still RED (expected). |
| OTL-T10 | F02: `dependent_null`, calendar ordering, cluster-robust cross-check. | T09 | A1 at 0.05, A2 at ρ 0.5 and A2 at ρ 0 all within tolerance; `test_position_boxed_orders_blocks_by_calendar_day` GREEN. |
| OTL-T11 | ADR-0049. F04: side-matched, dependence-aware fifth check with the selection/execution decomposition. | T10 | `test_fifth_check_refuses_coin_flip_on_drifting_paths` GREEN; A3 GREEN; fifth-check power ≥ 0.65. `make null --engine=day_boxed` now lists beats-always-long among the refusals. |
| OTL-T12 | ADR-0050. F05 LCB floor and `alternative_ev_net_r`; F06 widest-cell σ and the winner-σ measurement refusal. Update `controls.toml` (`[power] alternative_ev_net_r`; `[signal]` planted at it). | T10 | F05 and F06 tests GREEN; `test_lcb_floor_coverage` GREEN; `make signal` still ACCEPTED on both engines; `--schema` prints the new key with no value. |
| OTL-T13 | ADR-0051. F07 plateau. | T10 | F07 tests GREEN. |
| OTL-T14 | Regenerate `docs/console.html` and `docs/programme.html` (`make console`, `make programme`) **without changing any verdict**. New evidence fields render as "not recorded (pre-ADR-0048)". | T09–T13 | `make prepublish` clean; HEADS unchanged (the pages read the Registers, never write them). |

### Phase 3 — survey (1–2 weeks)

| Task | What | Depends on | Acceptance |
|---|---|---|---|
| OTL-T15 | ADR-0052. F08 Romano–Wolf on the cell×date matrix, the screen/validate split inside definition, and the shrunk margin column. | T10 | F08 tests GREEN, including `test_readiness_on_a_null_grid_passes_nothing` and the FWER and power slow tests. |
| OTL-T16 | F18 baseline-instability column and gate. | T15 | `test_readiness_flags_unstable_baseline` GREEN. |
| OTL-T17 | F22 strings; README partition wording. | — | `tests/test_docs.py` GREEN. |

### Phase 4 — integrity (1 week)

| Task | What | Depends on | Acceptance |
|---|---|---|---|
| OTL-T18 | ADR-0053. F09 structural overlap and data-set budget; stop auto-filling `distinction`. | T01 | F09 tests GREEN. |
| OTL-T19 | F10 lab ceiling, lab ledger and the `[lab].error_control` key. | T18 | F10 tests GREEN; the console shows lab spent/ceiling = 0.55/⟨author's ceiling⟩. |
| OTL-T20 | F12 locking and incremental verify. | T03 | F12 tests GREEN; a loop over 1,000 appends is linear (timing test with a generous bound). |
| OTL-T21 | ADR-0055. F14 `SOURCES.toml`, snapshots and `reproduce --at-source`. Done in the private history repository for the six verdict trees. | T08 | `test_every_resolved_names_a_known_source` GREEN. |

### Phase 5 — re-score the record under the conservative bundle (private, 1–2 days)

| Task | What | Depends on | Acceptance |
|---|---|---|---|
| OTL-T22 | G4 step 1 for Q-003, Q-004, Q-005, Q2-001, Q2-002 (and Q3-001's REGISTERED→MEASURED refusal): exact reproduction at the stamped commit or source snapshot. | T21 | Each prints an exact reproduction, or records `Rescored(reproduced=False, reason)`. |
| OTL-T23 | G4 step 3 under ADR-0048 to 0051: one `Rescored` per question in `register/diagnostics.jsonl`; re-pin and re-sign HEADS. | T22, T09–T13 | Six `Rescored` records. Q-003, Q-004, Q-005, Q2-002 and Q3-001 outcomes unchanged. Q2-001's diagnostic outcome recorded with every number (p, SE, LCB, winner σ, `need_w`). |
| OTL-T24 | Re-run the readiness computation for grid-001 and grid-002 under ADR-0052 from the recorded survey results (no new survey). Commit the new pages beside the old ones, labelled. | T15, T16 | `docs/surveys/grid-00{1,2}-…-readiness-adr0052.md` exist; the old pages are untouched. |
| OTL-T25 | Append a dated, record-derived note to `docs/LAB-CONCLUSION.md`. Write a new section; do not rewrite the adopted text. It quotes the `Rescored` records. | T23, T24 | The note cites diagnostics seq numbers; `make prepublish` clean. |

### Phase 6 — realism, non-conservative (weeks; data-dependent)

| Task | What | Depends on | Acceptance |
|---|---|---|---|
| OTL-T26 | ADR-0057. F16 stop slippage (required key) and cost curve; M5.0 reopened. Measure spreads with provenance. | T23 | F16 tests GREEN; `costs.basis="measured"` available. |
| OTL-T27 | ADR-0056. F15 point-in-time membership, or the survivorship diagnostic for sp_100 and dow_30. | T23 | F15 tests GREEN; a `SurvivorshipDiagnostic` for each single-name universe. |
| OTL-T28 | ADR-0058. F17 `ApparatusCalibrated` gate. | T05, T12 | `test_measure_refuses_without_calibration_for_this_code` GREEN. |
| OTL-T29 | Second G3 re-score of Q2-001 and Q2-002 with F15 and F16 **on top of** the conservative bundle. | T26, T27 | Two more `Rescored` records, each naming its full ADR set. |

### Phase 7 — hygiene (3–4 days, can run in parallel from Phase 1)

| Task | What | Depends on | Acceptance |
|---|---|---|---|
| OTL-T30 | F19 `test_core_usage`, `test_check_never_imports_boto3`. | — | GREEN. |
| OTL-T31 | ADR-0059. F21 entry registry and causality property test. | T07 | F21 tests GREEN; `docs/EXTENDING.md` §3 rewritten to the registry path. |
| OTL-T32 | F24 ruff widening, strict zips, leave-one-out refusal on non-positive pooled score, duplicate import. | — | `make lint` GREEN under the new selection; F24 tests GREEN. |
| OTL-T33 | F25 TASKS split and CLAUDE.md ≤ 5 KB. | — | `test_claude_md_is_small`, `test_tasks_has_no_status_log` GREEN. |

### Definition of done

1. ADR-0047 to ADR-0059 are adopted. Each names the fixes it covers and binds from the next registration.
2. Every test named in §3 exists. Every test marked RED was observed failing on `2e86d58` and now passes. `make check` is green locally and in CI, and the nightly `-m slow` job is green.
3. The apparatus size and power table (F23) shows, on both engines, for S ≥ 200 seeds:
   - beats-null size ≤ α + tol at α ∈ {0.01, 0.05} for ρ ∈ {0, 0.5};
   - fifth-check size ≤ α + tol on a drifting world;
   - LCB-floor coverage ≥ 1 − α_c − tol;
   - power ≥ planned − tol at the declared alternative.

   `ApparatusCalibrated` is recorded for the current `engine_code_sha`.
4. `make null` is refused by beats-null **and** beats-always-long on the day-boxed engine, not by the floor alone. `make signal` is accepted at the declared alternative.
5. `register/HEADS.toml` is committed, signed and OpenTimestamps-anchored. Forgery and truncation tests are green, and prepublish checks the heads.
6. No measurement can run on dirty or unknown code. Every new `HypothesisMeasured`, `HypothesisResolved` and `SurveyRecorded` carries `engine_code_sha` over the import closure.
7. `register/diagnostics.jsonl` holds one `Rescored` per historical question, each first reproduced exactly. No line of the three programme Registers has changed, which the heads pinned in T03 prove.
8. The readiness tables for grid-001 and grid-002 exist under ADR-0052 beside the originals. The README says "definition partition (30 %)" and "measurement partition (50 %)", and never "half".
9. `CLAUDE.md` ≤ 5 KB, and `TASKS-v4.md` holds the plan without the diary.

---

## Appendix A — probes (run against `2e86d58`)

All probes ran in a scratch venv (`pip install -e ".[dev]"`, Python 3.12.10), offline, without touching the repository. They are reproduced here so that OTL-T05 can turn them into tests.

**A1 — position_boxed null size (F01, F02, F04).** 200 seeds, about 150 s.
```python
world = {n: random_walk(n, days=1260, seed=seed, sigma_daily=0.02, drift_daily=-0.02**2/2) for n in "ABCDEFGH"}
t = StrategySpec(entries=(Entry(EntryKind.DOWN_RUN, Side.LONG, (("runs", 3),)),), exits=(Exit(ExitKind.TIME, (("bars", 5),)),),
                 stop=Stop(StopKind.PERCENT, 10.0), sizing=Sizing(), order_type=OrderType.MARKET, horizon=Horizon.MULTI_DAY,
                 universe=UniverseRule((("world", "probe"),)),
                 required_capabilities=frozenset({Capability.NATIVE_STOP, Capability.RESTING_ORDERS}), axis=InformationAxis.PRICE_DAILY)
m = position_boxed.measure(t, {"hold": [5.0]}, lambda t, p: t, world, seed=seed, cost_in_r=0.0, null_draws=2000)
p = (1 + sum(v >= m.winner.ev for v in m.null_ev)) / (1 + len(m.null_ev))
# "fixed-N": the same random-entry positions, moving-block resampled to length m.winner.n
```
Result: winner N ≈ 645, random-entry pool ≈ 2,035. beats-null false-positive rate: 0.140 at 0.01 and 0.225 at 0.05. Fixed-N: 0.015 and 0.100. beats-always-long: 0.065 and 0.135.

**A2 — day_boxed null under a common factor (F02).** 10 names, 1,260 days. Daily return = −σ²/2 + σ(√ρ·z_common + √(1−ρ)·z_name), σ 0.02. `down_run(2)`, intraday, time exit 1 bar, stop 5 %, zero cost, single cell, 200 seeds, about 300 s each.

| ρ | false positives at 0.01 | at 0.05 | winner N | distinct dates |
|---|---|---|---|---|
| 0.0 | 0.010 | 0.050 | about 3,192 | about 1,189 |
| 0.5 | 0.090 | 0.200 | about 3,185 | about 917 |

**A3 — fifth check on the day-boxed null control (F04).** `controls._day_boxed_measurement("null", load_controls(), seed=20260910, …)`.
- Winner `stop 4, target 3`: N 6,295, EV −0.0797; `baseline_ev` −0.1033; margin +0.0236.
- Baseline draws: mean −0.1031, sd 0.0090, so the check passes at α/9.
- `make null --engine=day_boxed` reports `checks that passed: ['plateau', 'leave_one_out', 'beats_always_long']`.

**A4 — Register forgery and truncation (F11).**
- Copy `register/programme-2.jsonl` and set the payload `outcome` of seq 33 (Q2-002) to `"supported"`.
- Recompute `sha = sha256(f"{prev}|{seq}|{canonical(payload)}")` and `prev` forward from genesis. `Store("forged.jsonl").verify()` returns 37.
- The first 20 lines alone verify as 20.

**A5 — numbers used in §4 (scipy, `occams.core.power`).**
- `n_for_mean_shift(0.15/2.2209, 0.01)` = 2,561 and `n_for_mean_shift(0.15/4.0947, 0.01)` = 8,704. Both match the registered `required_n` of Q2-001 and Q2-002.
- σ at which N = 6,946 is just powered: 3.658 R.
- LCB99 for Q2-001 at σ 2.2209: +0.1514 (iid), +0.1375 (deff 1.5), +0.1257 (deff 2). At σ 4.0947: +0.0991, +0.0734, +0.0518.
- Effective N needed for Q2-001's LCB99 ≥ 0.15 at σ 2.2209: 6,640.
- Bonferroni one-sided z over 38,976 cells at 0.05: 4.70.
- Q2-002: saving needed 0.0411 R = 8.2 bp of price at a 2 % stop, so the measured round trip must be ≤ 1.8 bp against the 10 bp bound.
