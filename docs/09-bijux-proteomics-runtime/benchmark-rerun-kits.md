---
title: Benchmark Rerun Kits
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-07-01
---

# Benchmark Rerun Kits

These rerun kits are the shortest path from public benchmark package root to
the strongest checked rerun lane for each workflow family.

The goal is not to list every artifact in the repository. The goal is to let an
independent reviewer reopen one family without guessing:

- which package root is primary
- which companion package adds real pressure
- which runtime entrypoint actually counts
- which remaining limits still keep the family bounded

## What Every Kit Must Provide

Each family kit should give a reviewer:

- one primary public package root
- one companion stress or transfer package
- one named runtime lane
- one clear run-mode statement
- one short list of remaining limits that still narrow the family sentence

## Family Kits

| family | current public posture | primary package | companion package | run mode | strongest remaining limiter |
| --- | --- | --- | --- | --- | --- |
| `dda` | outsider-auditable, bounded | `dda_reviewable_run` | `dda_cross_engine_review_package` | `import_only` | no in-repo live-engine parity yet |
| `dia` | outsider-auditable, bounded | `dia_library_review_package` | `dia_matrix_shift_review_package` | `raw_executable` | library incompleteness and downstream consequence still narrow the sentence |
| `lfq` | review-grade, bounded | `lfq_cohort_review_package` | `lfq_sparse_contrast_review_package` | `raw_executable` | missingness and cohort-transfer pressure still block stronger public language |
| `multiplex` | internal support only | `multiplex_tmtpro_review_package` | `multiplex_channel_stress_review_package` | `raw_executable` | outsider trust still collapses under the stress packet |
| `ptm` | outsider-auditable, bounded | `ptm_localization_review_package` | `ptm_ambiguity_stress_review_package` | `raw_executable` | consequence confidence remains weaker than localization strength |
| `targeted` | outsider-auditable, bounded | `targeted_transition_review_package` | `targeted_carryover_review_package` | `raw_executable` | calibration, interference, and burden still narrow stronger certainty |

## How To Open A Kit

For every family, use the same order:

1. open the primary package manifest and inventory
2. open the companion package manifest and inventory
3. open the named runtime rerun lane
4. inspect the rerun dossier or external review kit when the family publishes one
5. stop at the published limiter instead of improvising a stronger sentence

This is the point of the kit: a reviewer should not need maintainer folklore
to know where the rerun route begins or where it still stops.

## What The Kits Prove

- the current flagship families have explicit reopen paths rather than only
  descriptive trust prose
- paired-package pressure is part of the runtime story now, not a later
  documentation caveat
- run-mode honesty is visible at the rerun-kit layer instead of being buried in
  tests or implementation

## What The Kits Still Do Not Prove

- scientific truth independent of the benchmark and grounding layers
- vendor parity just because a raw-executable lane exists
- downstream assay worth just because the rerun lane is real

## Best Next Routes

- Open [Operator Rerun Journey](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/operator-rerun-journey/)
  for the shortest operator-facing opening order.
- Open [Execution](https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/execution-overview/)
  for the family-level runtime ceiling.
- Open [Benchmark Assets](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/benchmark-assets/)
  when the question becomes whether the public evidence root itself is strong
  enough.

## Boundary

This page owns family-level rerun opening order. It should not turn into a
second benchmark catalog or a second release-language page.
