---
title: Runtime Rerun Refusals
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-05-09
---

# Runtime Rerun Refusals

This ledger records when a nominal workflow family still cannot be rerun more faithfully because the repository stops at imported exports, proprietary steps, missing vendor-native inputs, or stronger consequence gaps.

## `dda`

- rerun ready: `no`
- refusal reasons: faithful rerun still stops at imported MaxQuant and comparator exports because the repository does not own a raw DDA search execution lane, external-engine behavior remains proprietary or out-of-repository for the strongest DDA package
- blocked claims: raw DDA search parity, full outsider-auditable DDA rerun language
- next evidence paths: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dda/failure_replay.json`
- note: The refusal ledger names exactly why a workflow family still stops short of a stronger rerun claim instead of letting maintainers narrate around the gap.

## `dia`

- rerun ready: `no`
- refusal reasons: the shipped DIA lane is raw-executable in runtime terms but still depends on library-conditioned exported reports rather than chromatogram-native replay
- blocked claims: chromatogram-native DIA parity, broad vendor-parity DIA authority
- next evidence paths: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dia_library_review_package/package_manifest.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/dia/failure_replay.json`
- note: The refusal ledger names exactly why a workflow family still stops short of a stronger rerun claim instead of letting maintainers narrate around the gap.

## `lfq`

- rerun ready: `yes`
- refusal reasons: none
- blocked claims: none
- next evidence paths: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/lfq_cohort_review_package/package_manifest.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/lfq/failure_replay.json`
- note: The refusal ledger names exactly why a workflow family still stops short of a stronger rerun claim instead of letting maintainers narrate around the gap.

## `multiplex`

- rerun ready: `no`
- refusal reasons: multiplex remains below outsider-auditable trust because runtime rerun strength still outruns family-level consequence and challenge closure
- blocked claims: outsider-auditable multiplex trust
- next evidence paths: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/multiplex_tmtpro_review_package/package_manifest.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/multiplex/failure_replay.json`
- note: The refusal ledger names exactly why a workflow family still stops short of a stronger rerun claim instead of letting maintainers narrate around the gap.

## `ptm`

- rerun ready: `yes`
- refusal reasons: none
- blocked claims: none
- next evidence paths: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/ptm_localization_review_package/package_manifest.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/ptm/failure_replay.json`
- note: The refusal ledger names exactly why a workflow family still stops short of a stronger rerun claim instead of letting maintainers narrate around the gap.

## `targeted`

- rerun ready: `yes`
- refusal reasons: none
- blocked claims: none
- next evidence paths: `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/targeted_transition_review_package/package_manifest.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/run_bundle.json`, `packages/bijux-proteomics-runtime/tests/fixtures/flagship_runs/targeted/failure_replay.json`
- note: The refusal ledger names exactly why a workflow family still stops short of a stronger rerun claim instead of letting maintainers narrate around the gap.
