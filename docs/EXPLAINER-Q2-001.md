# A strategy that passed four checks and turned out to be the market

*For a reader with no code. Every number is a record in
`register/programme-2.jsonl`, cited by its number; the same story is told
with the records beside it on `docs/programme.html` and in
`docs/PROGRAMME-2-CONCLUSION.md`.*

## What was asked

In September 2026 the lab screened 38,976 ways of entering and exiting a
trade — every mechanism its closed list could express, on four groups of
US stocks and funds, on the definition partition only, the oldest 30 % of the history, at no
cost to its error budget (record #9). From that screen the author chose
one cell and registered it as a question (#13): **after a four-day run
of lower closes on a large US stock, while the market's own trend
classifier says "up", buy at the next open and hold for a while.** The
floor was declared before anything ran: at least 0.15 units of risk per
trade after costs, at least fifty trades a year. So was the price: 0.15
of the programme's error budget, charged before a bar of the test half
was read (#12).

## What the machine found

On the measurement partition — the next 50 % of the history, which no one
had looked at — the strategy made
**+0.213 units of risk per trade after costs, over 6,946 trades, about
413 a year** (#19). It passed every check the lab then had:

- it beat random entry with the same holding rule, at the corrected
  significance;
- its neighbouring settings did about as well, so it was not one lucky
  parameter;
- leaving any one stock out did not break it;
- it cleared the floor.

Verdict: **supported.** The strategy moved to the state the lab calls
`FORWARD` (#22). By every rule in force that day, this was a finding.

## What the record beside it says

The lab writes one more record after every verdict (#24). It runs the
simplest possible alternative — **just be long, with the same holding
period, in the same "up" regime, on the same stocks, on the same test
half** — and puts the two side by side.

| | per trade, after costs |
|---|---|
| the strategy | +0.213 |
| just being long, same holding period and regime | +0.214 |
| the difference the entry made | **−0.001** |

The entry signal — the four-day run of lower closes — added nothing.
What the strategy captured was the market's own return during the years
its classifier called "up", 2003 to 2019, at the twenty-day holding
period its sweep had chosen because that was where the raw return was
largest. On the definition partition, the same comparison had shown a
comfortable margin of +0.239; on the measurement partition it vanished (#24).

## Why the checks did not see it

Each check asked a real question and got a true answer. *Better than
chance?* Yes — random entry with a coin-flip direction does worse than
being long in a rising market. *Robust across settings and stocks?* Yes —
so is being long. *Big enough?* Yes. None of them asked *better than the
obvious thing you could have done instead?* That is a different question,
and on the day the record showed it, the lab made it the fifth check
(ADR-0043) and began ranking every sweep by the margin over being long
rather than by raw return (ADR-0045) — for every question after this
one. This one was not re-judged; the verdict stands as reached, with the
record beside it.

## What happened next

The same mechanism without the regime gate was asked under the new rules
(#26–#33). Ranked by margin, its winner was the *short* holding period,
where being long earns little; it beat being long by +0.075 per trade —
the entry did earn something there — and missed the floor by 0.041.
Verdict: **null.** The author stopped the programme (#36): one winner
rule had said *yes, for the wrong reason*; the other had said *yes, not
enough*.

## What to take from it

A backtest that beats chance, holds across settings and stocks, and
clears a floor can still be measuring the market, not the idea. The
only defence is to ask, before the money moves, what the passive
alternative at exactly the same geometry would have made — and to write
the answer down beside the verdict whether it flatters the strategy or
not. This lab now does, by construction. Nothing here places an order.
