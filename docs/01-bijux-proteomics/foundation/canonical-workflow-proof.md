---
title: Canonical Workflow Proof
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-05-07
---

# Canonical Workflow Proof

`bijux-proteomics` now has one checked canonical workflow family:
`reviewable-proteomics`.

That phrase is intentionally narrow. It means one governed workflow proof set
exists from sequence intake through search/confidence, quantification, PTM
review, scientific-kernel review, evidence review, decision review, lab
handoff, and follow-up. It does **not** mean the repository now has broad
proteomics workflow coverage.

## Open First

The strongest shipped proof path currently starts with the DDA public package,
not with a governance report.

Open these files first:

- `packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/README.md`
- `packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/package_manifest.json`
- `packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/artifact_inventory.json`
- `packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/scientific_invariants.json`
- `packages/bijux-proteomics-core/tests/fixtures/public_benchmark_packages/dda_reviewable_run/warning_demonstrations.json`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/benchmark_runs.py`
- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/references/workflows/comparator_confrontations.py`

Those files show the actual current DDA proof surface:

- one raw-like spectrum
- one primary MaxQuant import lane
- one MSFragger comparator export
- explicit search settings
- numeric invariants
- one demonstrated protein-rollup warning

## What Exists Now

The current canonical proof set proves one narrow workflow story, and the DDA
public package is the clearest outsider-readable entrypoint into it:

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

## Claim Taxonomy

Workflow-facing claims in this repository should stay in one of four tiers:

- `owned_contract`
- `benchmark_backed_behavior`
- `runtime_proven_workflow`
- `future_work`

The canonical workflow proof set is the place where `runtime_proven_workflow`
claims are allowed. If a workflow family does not have a checked proof set with
artifact paths and validating tests, it should stay in `benchmark_backed_behavior`
or `future_work`.

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
It will come from stronger flagship evidence:

- more than one public benchmark package that outsiders can inspect from files
  alone
- stronger runtime execution families than the current import-only DDA and DIA
  lanes
- live-engine or broader multi-run comparator confrontation where the current
  package still stops at imported-result pressure
- decision and follow-up surfaces that continue to survive those harder public
  packages

## Boundary

Only `reviewable-proteomics` may be described with canonical workflow prose.
Every other workflow family remains future-only until it has its own
artifact-backed proof surface.
