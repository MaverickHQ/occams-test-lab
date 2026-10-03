# Approval is a signature, and the proposer never runs on the execution host

`APPROVED -> LIVE` is the safety-critical transition, and "human-only" is not
a property a machine can assert about itself. A CLI command, a touched file
and a Telegram reply are all forgeable by any agent holding the same shell
and the same credentials — and this project's research proposer reads
adversarial public text by design, so an injection reaching a shell is a real
path rather than a hypothetical one.

Two rules close it. **Approval is a cryptographic signature over the spec
hash**, made with a key whose passphrase is typed interactively at approval
time and stored nowhere a process can read. `LiveGate` verifies the
signature, not the existence of an approval record: an agent can create a
file, but it cannot produce a valid signature. **And the proposer never runs
on the execution host** — internet-reading code and order-submitting code
share no machine, no filesystem and no credential set.

## Considered options

- **Out-of-band approval from a second device**, with the executor polling a
  store it cannot write to. Stronger still, because the approving and trading
  devices share nothing. Deferred, not rejected: it needs real
  infrastructure and a second trust domain. Revisit if the operational
  footprint grows.
- **CLI or file approval on the same host.** Adequate against mistakes and
  mode errors, which are the likeliest failures, and forgeable by anything
  with a shell.

## Consequences

A passphrase is typed for every approval — deliberately, because approvals
should be rare and deliberate. Two environments must be maintained. The
host separation is free to adopt now and expensive to retrofit later, which
is why it is decided before any code exists.
