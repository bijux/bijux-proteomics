---
title: Release Support
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
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
- `src/bijux_proteomics_dev/release/governance/scientific_readiness.py`
- `src/bijux_proteomics_dev/release/governance/ssot_readiness.py`
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

Reviewers should be able to open one manifest and see:

- the owning package
- the benchmark id and checked-in dataset locator
- the builder symbol that produces the reviewable output
- the test path that proves the path
- the doc path that explains the scope
- the exact scientific limit summary that keeps the claim honest

Use `build_scientific_release_dossier()` when you need the live code-backed
index, and review
`configs/package-governance/scientific-release-workflows.toml` when you need
the checked-in declaration that release policy depends on.

Use `validate_ssot_readiness()` when the question is whether public symbol
ownership, duplicate model ownership, compatibility-bridge posture, and
package-boundary substance are all clean enough for scientific release claims
to count at all. Review
`docs/08-bijux-proteomics-maintain/bijux-proteomics-dev/package-substance.md`
when the question is whether the current package split still earns its
separate release identities.

## Design Pressure

The easy failure is to let release automation look authoritative even when the underlying version and publication rules are no longer explicit or aligned.
