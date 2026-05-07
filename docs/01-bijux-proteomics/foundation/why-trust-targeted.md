---
title: Why Trust Targeted
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-07
---

# Why Trust Targeted

This page is about the current flagship `targeted` surface.

The trustworthy part today is the explicit QC, calibration, and interference
limit surface. The repository does not yet earn a flagship outsider-auditable
targeted workflow claim.

## Open First

- `benchmark:targeted_transition_consistency`
- `packages/bijux-proteomics-core/tests/fixtures/formats/targeted_benchmark_qc.tsv`
- `packages/bijux-proteomics-lab/tests/fixtures/handoffs/supported_targeted_follow_up.json`
- `packages/bijux-proteomics-lab/tests/fixtures/handoffs/failed_targeted_transition_follow_up.json`
- `packages/bijux-proteomics-lab/tests/fixtures/handoffs/refused_targeted_follow_up.json`

## Current Trust Earned

- `outsider_review:targeted` is not complete enough to count as an
  outsider-auditable flagship family.
- benchmark evidence tier is `curated_mini_study`.
- public claim support is `refused`.
- no flagship runtime truth row is published for targeted yet.
- the recommendation posture is `do_not_recommend`.
- the lab posture is `not_worth_assay`.

## Exact Claims

- targeted benchmark outputs preserve transition-level QC evidence and explicit
  protein-inference caution across the bundled chromatogram fixture
- targeted review can support operator-facing QC interpretation without
  pretending to prove vendor-parity targeted biology

## What You Can Trust Right Now

- the QC and follow-up packet boundaries are explicit
- refusal is visible when calibration and interference realism remain too thin

## What You Should Not Trust Yet

- there is still no flagship runtime truth row for targeted
- comparator-backed public support is still refused
- this is still a curated mini-study rather than a flagship public package
