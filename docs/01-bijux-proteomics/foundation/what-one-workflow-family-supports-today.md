---
title: What One Workflow Family Supports Today
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-06-30
---

# What One Workflow Family Supports Today

This page exists to explain what one workflow family must contain before the
repository can give it a serious public sentence. The question is no longer
whether the repository has one thin canonical demo. The question is whether a
given family now has enough benchmark, runtime, grounding, recommendation, and
consequence depth to support bounded outsider-facing language.

That phrase remains intentionally narrow. One workflow family support packet
does **not** mean broad proteomics coverage. It means one family can now be
challenged end to end from tracked public surfaces without outsourcing the
explanation to maintainer memory.

## Open First

The strongest shipped evidence paths currently start with flagship public
packages, not with governance reports. DDA remains the clearest reader-first
example because its public benchmark, rerun, comparator, and consequence
surfaces still show the whole chain in one bounded route.

Open these files first:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/README.md`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/artifact_inventory.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/scientific_invariants.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/warning_demonstrations.json`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/benchmark_runs.py`
- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/references/workflows/comparator_confrontations.py`

Those files show one concrete current DDA support surface:

- one raw-like spectrum
- one primary MaxQuant import lane
- one MSFragger comparator export
- explicit search settings
- numeric invariants
- one demonstrated protein-rollup warning

## What Exists Now

The current repository supports several family packets at different public
strengths, and the DDA public package is still the clearest outsider-readable
entrypoint into the pattern:

- runtime-owned sequence, search/confidence, quantification, PTM, and lab
  handoff artifacts
- core-owned DDA public package with artifact inventory, invariant ledger, and
  warning ledger
- knowledge-owned benchmark manifest and comparator confrontation pinned to the
  same DDA public package
- intelligence-owned decision review with downgrade chains
- lab-owned follow-up packet with explicit progression blockers

Current reviewer anchors for that story:

- runtime lane:
  `dda-maxquant-pipeline-corpus`
- benchmark manifest:
  `benchmark:dda_search_reproducibility`
- comparator path:
  `comparator_path:msfragger_imported_dda_review`
- validating tests:
  `packages/bijux-proteomics-core/tests/benchmarks/test_dda_reviewable_package_surface.py`
  `packages/bijux-proteomics-runtime/tests/workflows/test_benchmark_runtime_surface.py`
  `packages/bijux-proteomics-knowledge/tests/references/test_references_benchmarks.py`

Current outsider-facing review pages for that story:

- `docs/01-bijux-proteomics/foundation/why-trust-dda.md`
- `docs/01-bijux-proteomics/foundation/flagship-release-candidate.md`
- `docs/01-bijux-proteomics/foundation/elite-readiness-scorecard.md`

## What A Real Family Packet Now Requires

- one flagship public benchmark package that can be opened without private
  maintainer context
- one runtime lane that makes execution realism and refusal visible
- one grounding and contradiction route that keeps the scientific sentence
  challengeable
- one recommendation packet that shows downgrade, confidence, or refusal
- one consequence packet that keeps requested-versus-observed follow-up and
  assay burden visible

## Claim Taxonomy

Workflow-facing claims in this repository should stay in one of four tiers:

- `owned_contract`
- `benchmark_backed_behavior`
- `runtime_proven_workflow`
- `future_work`

This page is where `runtime_proven_workflow` claims are allowed. If a workflow
family does not have a checked artifact-backed surface with validating tests,
it should stay in `benchmark_backed_behavior` or `future_work`.

## What This Does Not Mean

The canonical proof set does not authorize broad claims about:

- glycopeptide workflow coverage
- library-search scientific depth
- external-engine parity as solved scientific behavior
- broad cohort-grade DDA trust beyond the tracked imported-result package

Those remain explicit boundary-only surfaces until they have their own checked
proof sets.

## Reference-Grade Boundary

One undeniable workflow is necessary, but it is not enough by itself to make
the whole repository `reference-grade` or `elite`.

The next honest rise in posture will not come from more repository self-audit.
It will come from stronger family packets:

- more than one public benchmark package that outsiders can inspect from files
  alone
- stronger runtime execution families than the current import-only DDA and DIA
  lanes
- live-engine or broader multi-run comparator confrontation where the current
  package still stops at imported-result pressure
- decision and follow-up surfaces that continue to survive those harder public
  packages

## Strongest Companion Routes

- open
  [Workflow Claim Limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/workflow-claim-limits/)
  for the released sentence ceiling across families
- open
  [External Review Kits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/external-review-kits/)
  for the shortest outsider challenge route
- open
  [Current Capability Limits](https://bijux.io/bijux-proteomics/01-bijux-proteomics/foundation/current-capability-limits/)
  when a family packet looks stronger than the current release language

## Boundary

Only families with their own artifact-backed proof surfaces may be described
with this one-workflow-family sentence. Every stronger release claim still has
to pass through the family claim-limit and readiness surfaces.
