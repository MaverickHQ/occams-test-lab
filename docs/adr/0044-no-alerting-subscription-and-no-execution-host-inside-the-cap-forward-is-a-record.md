---
status: decided 2026-09-19 — drafted 2026-09-18 and adopted by the author the next day; M0.22 closed as a design change, no figure proposed (R9); M11.1–M11.3 closed as not built by decision; M10 closed as deferred with the execution host; `FORWARD` is a record
---

# No alerting subscription and no execution host inside the cap: FORWARD is a record

M0.14 recorded a go for M1–M10 on the default build and **two no-gos
inside the cap**: M11's TradingView line and the credentialed execution
host ADR-0030 describes. M0.22 asks that each be resolved either as a cap
decision — the author's alone, and no figure is proposed here — or as a
design change recorded in an ADR. This is the second kind, drafted for
the author to adopt, amend or refuse.

Two facts have arrived since M0.22 was written. **The lab has run a whole
programme and a half without either.** Four verdicts, three null and one
supported, were reached with no alert delivered and no order placed; the
console, the survey page, the programme page and the readiness table are
the lab's outputs, and each is a committed artifact rather than a live
feed. **The one supported verdict does not want a forward window.** Its
Strategy stands at `FORWARD` (programme 2, #22), and the record beside it
(#24) says the return it measures is being long in the up regime, not the
entry the sentence claims; ADR-0043 now makes that a check. A forward
window run on it would falsify a claim nobody is making.

## Decision (adopted 2026-09-19)

1. **The alerting path is the lab's own pages, not a subscription.** A
   signal the lab would once have sent to TradingView is a row on a
   committed page — the console's Strategy state and, when a forward
   window opens, its intents — rendered on every build. M11.1–M11.3 (the
   Pine derivation and its alert line) close as **not built, by
   decision**; the three Pine derivations ADR-0037 owes are owed to no
   one. The design's obligation that a reader with no code can see what
   the lab would do is met by the pages.
2. **The execution host is deferred outside this lab.** No credentialed
   host is built or priced here. `FORWARD` is a recorded state: the
   Strategy that reached it is named, hashed and frozen in the Register,
   and nothing trades. A forward window (ADR-0014) opens only when a host
   exists, priced and decided under its own M0, and the question of
   whether the Strategy at `FORWARD` deserves one is answered then, on the
   record as it stands. M10.9–M10.17 close as **deferred with the host**;
   M10.1–M10.8, the account envelope and the forward plumbing, close the
   same way — they are built when the host is, not before.
3. **The cap stays as declared.** Nothing here proposes a figure or a
   change to one (R9). If the author instead resolves either question as
   a cap decision, this ADR is refused and the rows reopen.

## Consequences

- M0.22 closes on adoption with a dated status-log entry naming this
  ADR; M11's milestone state becomes *closed by decision except M11.5–
  M11.6*, and M10's *deferred with the execution host*.
- `docs/M0-ANSWERS.md` is not edited: its no-gos stand as the record of
  2026-09-10; this ADR is the resolution the row asked for.
- The Strategy at `FORWARD` keeps its state. ADR-0014's rule — forward
  testing falsifies, it does not confirm — is untouched; it simply has
  nothing to run until a host exists.
- A later programme that wants alerts or execution reopens the question
  under its own M0 and its own cap, not by amending this record.

## Considered options

- **Pay for the TradingView line.** A cap decision, the author's; no
  figure here. Rejected in this draft because nothing the lab has done
  needed it, and a subscription that delivers alerts for a Strategy no
  one would trade is a cost with no reader.
- **Build a credentialed execution host now.** A cap decision and a
  recurring one (ADR-0030). Rejected in this draft: the only candidate
  Strategy's own record argues against trading it, and a host with no
  Strategy is the donor programme's mistake repeated.
- **Leave M0.22 open.** Rejected: an open row that gates nothing the lab
  does is a row the task list carries for no reason, and the milestone
  table has said "blocked inside the cap" for eight days of work that
  was not blocked.
