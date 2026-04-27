# PyPI Maintainer Notes

## Package identity

- package: `bijux-proteomics-foundation`
- import root: `bijux_proteomics_foundation`
- repository: `bijux/bijux-proteomics`
- owner: Bijan Mousavi (`bijan@bijux.io`)

## Release surface

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-foundation/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![Publish](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)

- package guide: <https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/>
- release and versioning: <https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/release-and-versioning/>
- package directory: <https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-foundation>
- verify workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml>
- release workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml>
- docs workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml>

## Release contract

- release must preserve canonical serialization determinism and schema
  compatibility behavior
- release docs must match the current ownership boundary and package identity
- downstream packages should not need behavioral rewrites unless the shared
  document contract intentionally changes

## Validation focus

- schema and serialization tests prove deterministic output behavior
- migration tests prove version-path continuity and failure diagnostics
- repository checks prove metadata, release wiring, and docs publication stay aligned

## Publication checkpoints

- package metadata, docs links, and ownership language should match the current
  shared primitive contract before tagging
- release validation should leave schema, migration, and serialization proof
  green in the repository root check surface
- the published wheel and sdist should reflect the same package identity and
  package guide that maintainers reviewed locally

## Release checklist

1. Confirm `README.md` reflects current package ownership and boundaries.
2. Confirm `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
   still match current schema ownership and migration behavior.
3. Run `make lint test quality security` from repository root.
4. Verify `.github/workflows/release-artifacts.yml` is configured for tag-triggered release (`v*`) with PyPI trusted publishing.
5. Create and push the release tag (`vX.Y.Z`) after changelog and metadata are final.
6. Confirm the release workflow uploaded and released both wheel and sdist artifacts.

## Explicit non-goals

- This page does not redefine schema compatibility semantics.
- This page does not replace package tests or release workflows.
