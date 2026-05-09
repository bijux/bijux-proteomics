---
title: Release Support
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-05-07
---

# Release Support

Release support should make version and publication rules visible before tags and workflows do the irreversible part.

## Release Model

```mermaid
flowchart TB
    release["release candidate"]
    version["version and changelog checks"]
    guard["publication guard"]
    publish["tag and publication may proceed"]

    release --> version
    version --> guard
    guard --> publish
```

This page should make release support feel like a pre-publication proof chain. The repository needs version logic, changelog discipline, and publication guards to agree before tags turn policy mistakes into published artifacts.

## Support Rules

- keep version resolution and changelog checks explicit
- block publication when repository proof is incomplete
- tie release decisions back to checked-in policy helpers
- require SSOT ownership readiness before any benchmark-backed scientific release claim can count as publishable
- require one checked-in scientific release dossier that names the owner,
  benchmark, tests, docs, and scientific limit for each workflow family

## First Proof Check

- `src/bijux_proteomics_dev/release/versioning/version_resolver.py`
- `src/bijux_proteomics_dev/release/versioning/changelog_version.py`
- `src/bijux_proteomics_dev/release/governance/publication_guard.py`
- `src/bijux_proteomics_dev/release/governance/repository_truth.py`
- `src/bijux_proteomics_dev/release/governance/workflow_lab_consequence.py`
- `src/bijux_proteomics_dev/release/governance/workflow_public_scrutiny.py`
- `src/bijux_proteomics_dev/release/governance/scientific_readiness.py`
- `src/bijux_proteomics_dev/release/governance/generated_governance_freshness.py`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/proof_accounting.py`
- `src/bijux_proteomics_dev/release/governance/ssot_readiness.py`
- `configs/package-governance/canonical-workflow-manifest.toml`
- `configs/package-governance/scientific-release-workflows.toml`

## Scientific Proof Chain

The release dossier is intentionally narrow. It covers the benchmark-backed
workflow families that the suite can defend today:

- `dda`
- `dia`
- `ptm`
- `lfq`
- `multiplex`
- `targeted`

Outsider-auditable workflow families today: `dda`, `dia`, `lfq`, `ptm`, `targeted`.
Internal-support-only workflow families today: `multiplex`.

For the strongest current outsider-readable proof, start with the DDA package
before reading the release policy helpers:

- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/README.md`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/package_manifest.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/scientific_invariants.json`
- `packages/bijux-proteomics-core/benchmark-assets/flagship-public-packages/dda_reviewable_run/warning_demonstrations.json`
- `packages/bijux-proteomics-runtime/src/bijux_proteomics_runtime/workflows/benchmark_runs.py`
- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge/references/workflows/comparator_confrontations.py`

Reviewers should be able to open one manifest and see:

- the owning package
- the benchmark id and checked-in dataset locator
- the builder symbol that produces the reviewable output
- the test path that proves the path
- the doc path that explains the scope
- the exact scientific limit summary that keeps the claim honest

For `dda`, the release conversation should now point directly to:

- `benchmark:dda_search_reproducibility`
- `benchmark_package:dda_reviewable_run`
- `dda-maxquant-pipeline-corpus`
- `comparator_path:msfragger_imported_dda_review`
- `docs/01-bijux-proteomics/foundation/flagship-release-candidate.md`
- `docs/01-bijux-proteomics/foundation/elite-readiness-scorecard.md`

Use `build_scientific_release_dossier()` when you need the live code-backed
index, and review
`configs/package-governance/scientific-release-workflows.toml` when you need
the checked-in declaration that release policy depends on.

Use `build_repository_truth_report()` when the question is stronger than
package publication and benchmark scope: it answers whether the repository may
honestly speak in `reference-grade` or `elite` language at all.

That repository truth now includes the runtime flagship proof gate. If the
strongest current runtime lane for a workflow family still depends on a fake
helper anywhere in its claimed flagship path, the family must not count toward
outsider-auditable or release-candidate authority.

That repository truth also includes the lab-consequence gate. A workflow family
must not be called lab-consequential unless the authority surface points to one
shipped requested-versus-observed outcome dossier and one assay-worth-it ledger
row for that same family.

When the question is specifically whether a runtime lane is raw,
import-backed, replay-backed, or simulation-only, open
`docs/09-bijux-proteomics-runtime/runtime-proof-accounting.md` before
generalizing from runtime success.

That report should not be the first stop for workflow trust. First open the
flagship package, runtime lane, comparator surface, and validating tests. Then
use repository truth to decide how far the repository may generalize from those
artifacts.

The current repository-wide language boundary is stricter than the strongest
current outsider packet:

- five bounded outsider-auditable workflow families exist
- multiplex remains internal support only
- repository-wide elite language is still blocked
- the scorecard for that boundary lives in
  `docs/01-bijux-proteomics/foundation/elite-readiness-scorecard.md`
- the paired scrutiny pages for that boundary now live in
  `docs/01-bijux-proteomics/foundation/what-breaks-elite-trust.md` and
  `docs/01-bijux-proteomics/foundation/what-earns-elite-trust-next.md`
- the public opening-order registry now lives in
  `docs/01-bijux-proteomics/foundation/public-artifact-index.md`

Use `validate_generated_governance_freshness()` before release to make sure
the generated governance reports under `configs/package-governance/` are still
fresh instead of silently stale.

Use `validate_workflow_public_scrutiny()` when the question is whether the
external review kits, artifact index, trust-boundary pages, and stronger
release language are still aligned.

Use `validate_ssot_readiness()` when the question is whether public symbol
ownership, duplicate model ownership, compatibility-bridge posture, and
package-boundary substance are all clean enough for scientific release claims
to count at all. Review
`docs/08-bijux-proteomics-maintain/bijux-proteomics-dev/package-substance.md`
when the question is whether the current package split still earns its
separate release identities.

## Design Pressure

The easy failure is to let release automation look authoritative even when the underlying version and publication rules are no longer explicit or aligned.
