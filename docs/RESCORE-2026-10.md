# The re-score of October 2026

**This document has no standing.** It is written from `register/diagnostics.jsonl` and nothing else, and nothing in it is a verdict. The six questions of this lab were resolved, or refused, under the rules in force when they ran; those records are sealed and none of them is changed here (ADR-0047). An external review then found the rules looser than they claimed, and they were corrected, forward only. This is what the corrected rules would have said, beside the record.

The store holds 6 records and its head is `b64adb55f687`. Each record names the rule set it was judged under in full, the commit and the content hash of the code that judged it, and every number of every check, passing or failing.

## How each question was treated

1. **Recreated first.** The question was measured again in the code of the commit its record stamps, from that commit's snapshot (`SOURCES.toml`), and compared with the record: the winner, its EV, its count, the checks that refused it. A question not recreated exactly is not re-scored.
2. **Then judged again**, by the present code, on the same bars and the stamped seed.
3. **Only on what it declared.** The floor's lower confidence bound needs no new number and is judged against the recorded floor. No question declared a slack in standard errors or an alternative to plan its power against: those are reported, not judged.

## At a glance

| Question | As recorded | Recreated from its source | Under the corrected rules |
|---|---|---|---|
| `Q-003` | null, EV -0.047 R over 1,391 trades; refused by beats-null, floor, leave-one-out | exactly | would be null; refused by beats-null, floor, leave-one-out, beats-always-long |
| `Q-004` | null, EV -0.045 R over 2,088 trades; refused by plateau, beats-null, floor, leave-one-out | exactly | would be null; refused by plateau, beats-null, floor, leave-one-out, beats-always-long |
| `Q-005` | null, EV +0.051 R over 893 trades; refused by floor, leave-one-out | exactly | would be refused at measurement, underpowered at its own dispersion; of the five checks, refused by beats-null, floor, leave-one-out, beats-always-long |
| `Q2-001` | supported, EV +0.213 R over 6,946 trades; no check refused it | exactly | would be null; refused by floor, beats-always-long |
| `Q2-002` | null, EV +0.109 R over 12,732 trades; refused by floor | exactly | would be null; refused by floor |
| `Q3-001` | refused at measurement: 863 trades against 1,068 required | no | not re-scored: its refusal stamps no engine |

## Question by question

### Q-003

Annotates record #9 of `register.jsonl` (`4bec6db4fbde`).

**Recreated exactly** at `e2cdf14d9281`: EV -0.0466 R over 1,391 trades, refused by beats-null, floor, leave-one-out.

**Under ADR-0043, ADR-0045, ADR-0048, ADR-0049, ADR-0050, ADR-0051, ADR-0055**, seed 20260911, 4,000 draws, code `0081ed652301` (content `be61a3e4d64d70dd`): **would be null**.

- The winner is cell [1, 0] — the recorded winner — with 1,391 trades, EV -0.047 R, its passive alternative -0.033 R, margin -0.014 R.
- At measurement: passes. Its own dispersion is 0.16 R against a plan of 1.20; its 1,391 trades are worth 921 independent ones.
- **plateau** passes: the winner is +0.012 R over its neighbours' median against a slack of 0.10, 2.15 of its standard errors (recorded, not judged).
- **beats-null** refuses: p 0.9883 by the bootstrap and 0.9896 by the clustered standard error, against 0.0100; a coin's side makes -0.034 R.
- **floor** refuses: the lower confidence bound is -0.059 R against a floor of +0.15; 82.8 trades a year against 50.
- **leave-one-out** refuses: fewer than three groups, so robustness cannot be shown.
- **beats-always-long** refuses: the passive alternative makes -0.033 R; the margin of -0.014 is +0.067 selection and -0.081 execution; p 0.9908 and 0.9917 against 0.0100.

### Q-004

Annotates record #21 of `register.jsonl` (`7d6814ef0aa1`).

**Recreated exactly** at `b145d49a7c7e`: EV -0.0451 R over 2,088 trades, refused by beats-null, floor, leave-one-out, plateau.

**Under ADR-0043, ADR-0045, ADR-0048, ADR-0049, ADR-0050, ADR-0051, ADR-0055**, seed 1, 4,000 draws, code `0081ed652301` (content `be61a3e4d64d70dd`): **would be null**.

- The winner is cell [1] — the recorded winner — with 2,088 trades, EV -0.045 R, its passive alternative -0.033 R, margin -0.013 R.
- At measurement: passes. Its own dispersion is 0.16 R against a plan of 1.20; its 2,088 trades are worth 1039 independent ones.
- **plateau** refuses: a neighbourhood of 2 against the 4 declared.
- **beats-null** refuses: p 0.9910 by the bootstrap and 0.9889 by the clustered standard error, against 0.0100; a coin's side makes -0.034 R.
- **floor** refuses: the lower confidence bound is -0.056 R against a floor of +0.15; 124.3 trades a year against 50.
- **leave-one-out** refuses: the pooled score is not positive; leave-one-out has nothing to preserve.
- **beats-always-long** refuses: the passive alternative makes -0.033 R; the margin of -0.013 is +0.063 selection and -0.075 execution; p 0.9923 and 0.9927 against 0.0100.

### Q-005

Annotates record #32 of `register.jsonl` (`287691f54b73`).

**Recreated exactly** at `e05a659dceaf`: EV +0.0513 R over 893 trades, refused by floor, leave-one-out.

**Under ADR-0043, ADR-0045, ADR-0048, ADR-0049, ADR-0050, ADR-0051, ADR-0055**, seed 20260911, 4,000 draws, code `0081ed652301` (content `be61a3e4d64d70dd`): **would be refused at measurement**.

- The winner is cell [1, 0] — the recorded winner — with 893 trades, EV +0.051 R, its passive alternative +0.022 R, margin +0.029 R.
- At measurement: refused — underpowered at the winning cell's own dispersion (ADR-0050). Its own dispersion is 0.91 R against a plan of 1.20; its 893 trades are worth 334 independent ones, and its own dispersion requires 431.
- **plateau** passes: the winner is +0.014 R over its neighbours' median against a slack of 0.10, 0.35 of its standard errors (recorded, not judged).
- **beats-null** refuses: p 0.0370 by the bootstrap and 0.0394 by the clustered standard error, against 0.0100; a coin's side makes -0.035 R.
- **floor** refuses: the lower confidence bound is -0.065 R against a floor of +0.15; 53.2 trades a year against 50.
- **leave-one-out** refuses: without IWM the score is -0.008 against +0.029 pooled.
- **beats-always-long** refuses: the passive alternative makes +0.022 R; the margin of +0.029 is +0.029 selection and +0.000 execution; p 0.2419 and 0.2394 against 0.0100.

### Q2-001

Annotates record #19 of `programme-2.jsonl` (`37327a3559ec`).

**Recreated exactly** at `1a243e504eb4`: EV +0.2134 R over 6,946 trades, refused by nothing.

**Under ADR-0043, ADR-0045, ADR-0048, ADR-0049, ADR-0050, ADR-0051, ADR-0055**, seed 20260917, 4,000 draws, code `0081ed652301` (content `be61a3e4d64d70dd`): **would be null**.

- The winner is cell [2, 0] — **not** the recorded winner: the surface is the margin now (ADR-0045, ADR-0049) — with 7,642 trades, EV +0.091 R, its passive alternative +0.037 R, margin +0.054 R.
- At measurement: passes. Its own dispersion is 1.51 R against a plan of 2.22; its 7,642 trades are worth 1566 independent ones.
- **plateau** passes: the winner is +0.012 R over its neighbours' median against a slack of 0.10, 0.42 of its standard errors (recorded, not judged).
- **beats-null** passes: p 0.0007 by the bootstrap and 0.0001 by the clustered standard error, against 0.0100; a coin's side makes -0.052 R.
- **floor** refuses: the lower confidence bound is +0.002 R against a floor of +0.15; 454.1 trades a year against 50.
- **leave-one-out** passes: without CRM the score is +0.050 against +0.054 pooled.
- **beats-always-long** refuses: the passive alternative makes +0.037 R; the margin of +0.054 is +0.054 selection and +0.000 execution; p 0.0310 and 0.0294 against 0.0100.

### Q2-002

Annotates record #33 of `programme-2.jsonl` (`bb6c9b72b0ee`).

**Recreated exactly** at `8f81ff3599fe`: EV +0.1089 R over 12,732 trades, refused by floor.

**Under ADR-0043, ADR-0045, ADR-0048, ADR-0049, ADR-0050, ADR-0051, ADR-0055**, seed 20260919, 4,000 draws, code `0081ed652301` (content `be61a3e4d64d70dd`): **would be null**.

- The winner is cell [2, 0] — the recorded winner — with 12,732 trades, EV +0.109 R, its passive alternative +0.034 R, margin +0.075 R.
- At measurement: passes. Its own dispersion is 1.79 R against a plan of 4.09; its 12,732 trades are worth 1965 independent ones.
- **plateau** passes: the winner is +0.016 R over its neighbours' median against a slack of 0.10, 0.55 of its standard errors (recorded, not judged).
- **beats-null** passes: p 0.0002 by the bootstrap and 1.1e-05 by the clustered standard error, against 0.0100; a coin's side makes -0.056 R.
- **floor** refuses: the lower confidence bound is +0.015 R against a floor of +0.15; 756.5 trades a year against 50.
- **leave-one-out** passes: without BLK the score is +0.071 against +0.075 pooled.
- **beats-always-long** passes: the passive alternative makes +0.034 R; the margin of +0.075 is +0.075 selection and +0.000 execution; p 0.0052 and 0.0056 against 0.0100.

### Q3-001

Annotates record #12 of `programme-3.jsonl` (`f4fd2b572b24`).

**Not recreated, so not re-scored.** The refusal at measurement stamps no engine commit: there is no stamped source to recreate its count from, and a question that is not recreated is not re-scored (ADR-0047 §4).

## What this is not

- **Not a verdict.** No outcome in any Register changed. The falsifier's count and every alpha balance are what they were.
- **Not a second look that spends nothing.** A re-score reads the measurement partition again. ADR-0047 §5 admits it on one condition, that a null is never revived on a guard set known to be too loose. No check that refused a question as recorded passes it here, and no outcome reads better than its record.
- **Not complete.** It does not correct for the survey's selection of its candidates, for questions that share a partition, or for today's members measured on earlier history. Those are the successor lab's (README, *Known limitations*).
