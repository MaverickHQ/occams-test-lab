---
status: amends ADR-0001
---

# Hypotheses come in two tiers: mechanism and implementation

ADR-0001 required a Strategy to cite a resolved Hypothesis without saying how
many Strategies one Hypothesis licenses. Both extremes fail. **Free** lets a
single confirmed mechanism justify twenty deployed variants, which is the
multiple-comparisons problem re-entering through the deployment door.
**Strictly one-to-one** means any spec change — a different universe rule, a
wider disaster stop — requires re-establishing the mechanism from scratch at
full alpha, which makes ordinary iteration unaffordable and invites working
around the rule.

The donor register already contains both kinds of question. Mechanism:
`X2-OVERNIGHT-GAP`, `C2-MAE-PREDICTABLE`, `X1-COMPRESSION`. Implementation:
`Z04-ORB-OBTAINABLE`, `Z-ENTRY-IMPLEMENTABLE`, `E3-COSTS`.

**A mechanism Hypothesis establishes the effect and carries the large alpha.
Each Strategy built on it registers its own implementation Hypothesis — does
*this* spec clear its floor net of costs and obtainability — at a smaller
declared allocation, and cannot exist without a resolved mechanism parent.**

## Consequences

The family stays bounded and countable. Variants cost something, which stops
twenty of them appearing; they do not cost everything, which stops the
discipline being abandoned as unworkable.

The mechanism and implementation per-test allocations are numbers that must
be justified rather than derived, and they are the obvious place for the
discipline to erode. They belong in configuration beside each axis budget.
Both draw from that one axis budget after search correction; they are not
additional top-level pools and are therefore never counted twice. Config load
enforces `sum(axis budgets) + reserve == total`, and registration refuses any
spend that would exceed the remaining axis budget.
