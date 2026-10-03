# Signed approvals are the only thing that crosses to execution

Splitting research from execution (ADR-0009) is undone by a shared writable
store: if the proposer can write anywhere the executor reads, injected
content has a path to the executor and only the physical separation survives.
The separation must be **directional**.

| direction | what may cross |
|---|---|
| research -> execution | **signed approvals only**, verified before the executor acts |
| execution -> research | fills, positions and state as schema-validated **data, never commands** |
| either | no filesystem mounts |

The signature from ADR-0009 therefore does double duty: it is the human gate
*and* the trust boundary between machines. The executor's rule reduces to one
sentence — **act only on things bearing a valid signature** — and everything
else arriving from the research side is inert.

Fills flow back because the research host needs them to evaluate the forward
window (ADR-0014) and to measure live correlation at approval (ADR-0019).
That is the lower-risk direction: research is the less privileged host.

## Considered options

- **A shared store both hosts read and write.** Simplest transport and one
  place to look. It restores exactly the injection route the split closed.
- **One host with process isolation** — separate users and containers under
  the same directional rules. Much less work and adequate against mistakes
  and mode errors, which are the likeliest failures; not adequate against an
  injection achieving local privilege escalation. Kept on record as the
  fallback if running two machines proves impractical.

## Consequences

Two machines to run, patch and pay for, and a transport to build between
them.
