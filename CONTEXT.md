# Occams

A research lab that looks for tradeable edge and refuses to believe things
that are not true. It produces two kinds of output: resolved questions about
the world, and strategies that may be deployed against real capital.

## Language

### The two things that move

**Hypothesis**:
A registered question about the world, with a stated mechanism, both
interpretations, and a falsifier. It resolves exactly once and costs alpha.
_Avoid_: Idea, thesis, experiment, candidate

**Strategy**:
A deployable specification that trades. It is built as the apparatus for
measuring a Hypothesis, and becomes deployable only once that Hypothesis
resolves in its favour. It costs money, not alpha.
_Avoid_: Algo, bot, system, candidate

**Verdict**:
The one-time resolution of a Hypothesis against the detectable floor that was
declared before it ran. A null verdict is a result, not a failure.
_Avoid_: Outcome, conclusion, finding

**Refusal**:
A guard's recorded decision not to let something proceed, carrying a reason
and its evidence. Refusals are appended, never discarded — the contents of
the bin are what make the alpha arithmetic honest.
_Avoid_: Rejection, error, failure, bin

**StrategySpec**:
The frozen, declarative definition of a Strategy — entries, exits, mandatory
stop, sizing, order type, horizon, point-in-time UniverseRule, required
capabilities, and information axis. The single source of truth from which
every other representation is generated.
_Avoid_: Config, params, settings, rules

**Spec hash**:
The identity of a StrategySpec. Recorded in the Verdict at resolution and
asserted at deployment. Two specs with different hashes are different
strategies, however small the difference looks.
_Avoid_: Version, fingerprint

### Measurement

**R**:
The planned money at risk on a position, fixed by configuration in account
currency and converted to the instrument's currency at entry. Position size
is derived as R divided by stop distance, both in instrument currency.
Results are expressed as multiples of planned R, so a position that gaps
through its stop is recorded as worse than -1R.
_Avoid_: Risk unit, unit risk, 1R

**Detectable floor**:
The smallest effect worth acting on, declared as a pair — EV per trade in net
R, and a minimum trade frequency — before anything runs. A sample that cannot
see it is not measured.
_Avoid_: Threshold, hurdle, minimum edge, bar

**Net R**:
EV per trade after all costs — spread, commission, funding and FX conversion
spread — measured in the instrument's currency and divided by planned R
converted at entry. FX drift is excluded and reported as a separate exposure.
The unit every floor and verdict is stated in. Money is projected from it,
never declared.
_Avoid_: Edge, expectancy, return

### Data

**As-printed price**:
The price as it was published at the time, never restated. The only price
series the engine measures against.
_Avoid_: Raw price, unadjusted close

**Corporate action**:
A dated split, dividend, delisting, or acquisition term, carried as its own
event series. A price move explained by one is not a gap and does not fire a
stop; a delisting closes a position on its recorded terms.
_Avoid_: Adjustment, split factor

**Regime**:
A causal label for market state — ranging, uptrend, downtrend — computable at
time t from data no later than t. Its definition is frozen before any
strategy question and is not a free parameter of one.
_Avoid_: Market condition, environment, state

**Definition period**:
The earliest slice of history, spent on fixing pre-committed components such
as the regime classifier. Permanently excluded from strategy measurement.
_Avoid_: Training set, in-sample

**Measurement period**:
The slice of history on which hypotheses are measured and verdicts reached.
_Avoid_: In-sample, backtest window

**Reserve**:
A sealed slice of recent history. One look is permitted per spec hash, ever;
the look is recorded and a second is refused.
_Avoid_: Holdout, test set, validation set

**Forward period**:
Wall-clock time from entry into `FORWARD` — after the single reserve look and
**before** approval. The only genuinely unseen data. Not a slice of the
archive and carries no split percentage.
_Avoid_: Paper trading, out-of-sample
_Corrected 2026-09-06_ (ADR-0031). Previously read "from approval onward", which contradicted the state machine.

### The record

**Register**:
The append-only scientific record: hypotheses, declared floors, verdicts in
net R, refusals, alpha spend, spec hashes, reserve looks. Contains no account
currency and no account state, so it is publishable as it stands.
_Avoid_: Database, archive, results, log

**Operations log**:
The append-only operational record: orders, fills, money amounts, position
state, reconciliation. Never published.
_Avoid_: Trade log, journal, audit log

**Supersession**:
An explicit, recorded decision that a later Hypothesis replaces an earlier
one. The only legitimate way a resolved question is revisited.
_Avoid_: Retraction, revision, update

### Operation

**Approval**:
A signature over a spec hash, made by a human with a key whose passphrase is
never stored. The only thing that moves a Strategy to live.
_Avoid_: Sign-off, authorisation, go-ahead

**Retirement rule**:
The condition, declared at approval and derived from the Strategy's own Monte
Carlo path distribution, under which it stops trading. Evaluated
mechanically, never judged in the moment.
_Avoid_: Stop-out, cut-off, kill criteria

**Lab falsifier**:
The count of resolved mechanism verdicts, and the outcome, at which the whole
lab closes. Declared before the first Hypothesis resolves, evaluated
mechanically against the Register, never judged in the moment. Distinct from
alpha exhaustion, which stops the search and is repaired by new data; this
stops the enterprise and is not.
_Avoid_: Kill switch, sunset, exit criteria, giving up

**Halt**:
An immediate, unilateral stop that any human may trigger without
justification. Distinct from retirement: a halted Strategy may resume, a
retired one may not.
_Avoid_: Pause, disable, kill

**Required capabilities**:
What a Strategy needs from any venue in order to behave as measured — native
stop, resting orders, share granularity. Part of the Strategy's identity; the
broker that provides them is not.
_Avoid_: Broker features, venue support

**Calibration campaign**:
Trading at minimum size purely to measure real fill costs. A capability
question, not a market one, so it costs money and no alpha.
_Avoid_: Test trades, pilot, dry run

**Entry kind**:
A member of the closed `EntryKind` enum: one signal formula over the bars
before the box, one geometry row, one parameter list. A kind is a family
of questions; it is added only by an ADR that states the mechanism it
exists to test (ADR-0037). A kind is added, never discovered.
_Avoid_: Indicator, setup, pattern, signal type

**Draft**:
A proposed Hypothesis emitted by a proposer, carrying a mechanism and a
falsifier. It has no standing until a human confirms its registration, which
is the act that spends alpha.
_Avoid_: Idea, suggestion, candidate

**Known-at instant**:
The UTC moment a fact became available. A bar may be used only if its close
instant is strictly later. Dates are for reading, never for deciding.
_Avoid_: As-of date, effective date, timestamp

**Portfolio envelope**:
The declared maximum drawdown across everything live at once, distinct from
any single Strategy's. Breaching it halts every Strategy and retires none.
_Avoid_: Account drawdown, total risk, exposure limit

**Mechanism hypothesis**:
A question about whether an effect exists. Carries the large alpha and may
parent several implementation hypotheses.
_Avoid_: Theory, principle, finding

**Implementation hypothesis**:
A question about whether one specific Strategy clears its floor net of costs
and obtainability. Cannot exist without a resolved mechanism parent, and
spends the configured implementation per-test allocation from its parent's
information-axis budget.
_Avoid_: Build test, validation
