# Occams v4 alignment record

This record is non-normative. It shows where each prior review finding is resolved
and which executable task prevents the wording from drifting away from the
implementation. The normative order is ADR amendment, requirements, design,
then task evidence; a contradiction blocks release.

| Concern | Canonical v4 decision | Design and proof |
|---|---|---|
| Net R currency | Net R is measured in instrument currency after costs; FX conversion spread is a cost and FX drift is a separate exposure (ADR-0026, CONTEXT, R domain model) | D25; M5.3-M5.4 |
| Two-tier alpha | Each axis has one finite budget. Mechanism and implementation hypotheses use distinct configured per-test allocations charged to that same budget; child rates are never extra pools (ADR-0027, R4) | D3, D14; M6.2-M6.7, M8.1, M8.4 |
| Venue capabilities | Required capabilities are identity and venue is context, but adapter self-declaration is insufficient. Current conformance evidence is required at `COMPILED` (ADR-0018, F13) | D24; M0.12, M10.10-M10.11 |
| Data rights and reproduction | Exact reproduction uses the private licensed archive. Public reproduction uses raw bars only when redistribution is permitted; otherwise it proves the pipeline on redistributable or synthetic fixtures without claiming the historical Verdict (ADR-0021, F14, F18.7) | D12; M0.3-M0.6, M4.9, M11.5-M11.7 |
| Total affordability | The $150 cap covers the complete programme, not only data. A partial data-budget pass cannot start M1 (N5, Q11) | H4; M0.14 |
| Portfolio breach | A portfolio-envelope breach halts every Strategy and retires none. Resumption requires clearance, review, and a recorded human action for still-approved Strategies (ADR-0019, ADR-0024, F19) | D20-D21; M10.2, M10.15 |
| Strategy identity | `StrategySpec` and its hash contain a point-in-time `UniverseRule` and required capabilities, not a current instrument list. Resolved dated membership is context (ADR-0007 as amended by ADR-0018 and ADR-0025) | D4, D8; M3.1, M3.5, M4.10 |

## Snapshot checks

- The folder contains `REQUIREMENTS-v4.md`, `DESIGN-v4.md`,
  `TASKS-v4.md`, `CONTEXT.md`, this record, and all 27 ADRs.
- References inside the active planning documents point to v4 files and the
  local ADR snapshot.
- Historical version names appear only in `supersedes` metadata.
- No task may mark a milestone complete while a standing check is failing.
