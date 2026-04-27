# PyPI Maintainer Notes

## Package identity

- package: `bijux-proteomics-knowledge`
- import root: `bijux_proteomics_knowledge`
- repository: `bijux/bijux-proteomics`
- owner: Bijan Mousavi (`bijan@bijux.io`)

## Release surface

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-knowledge/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![Publish](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)

- package guide: <https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/>
- release and versioning: <https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/release-and-versioning/>
- package directory: <https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-knowledge>
- verify workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml>
- release workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml>
- docs workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml>

## Release contract

- release must preserve evidence, claim, and contradiction semantics without
  drifting into lifecycle or ranking ownership
- release docs must match the package boundary around trust, lineage, and resolution
- downstream packages should still depend on this layer for evidence semantics

## Validation focus

- evidence, resolution, and graph tests prove auditable semantics
- schema and serialization tests prove durable artifact compatibility
- repository release checks prove metadata, docs publication, and workflows stay aligned

## Publication checkpoints

- package metadata, docs routes, and evidence-ownership language should match
  the current trust and lineage contract before tagging
- release validation should leave evidence, resolution, graph, and schema proof
  green in the repository root check surface
- the published wheel and sdist should reflect the same import root and package
  guide that maintainers reviewed locally

## Release checklist

1. Confirm docs and README describe current evidence and conflict semantics.
2. Confirm `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
   still describe the same evidence and resolution ownership.
3. Run `make lint test quality security` from repository root.
4. Verify `.github/workflows/release-artifacts.yml` is configured for tag-triggered release (`v*`) with PyPI trusted publishing.
5. Create and push the release tag (`vX.Y.Z`) after changelog and metadata are final.
6. Confirm the release workflow uploaded and released both wheel and sdist artifacts.

## Explicit non-goals

- This page does not redefine evidence trust policy.
- This page does not replace graph, resolution, or schema tests.
