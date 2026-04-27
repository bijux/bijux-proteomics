# PyPI Maintainer Notes

## Package identity

- package: `bijux-proteomics-core`
- import root: `bijux_proteomics`
- repository: `bijux/bijux-proteomics`
- owner: Bijan Mousavi (`bijan@bijux.io`)

## Release surface

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-core/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![Publish](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)

- package guide: <https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/>
- release and versioning: <https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/release-and-versioning/>
- package directory: <https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-core>
- verify workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml>
- release workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml>
- docs workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml>

## Release contract

- release must preserve lifecycle semantics, validator diagnostics, and domain
  ownership boundaries
- release docs must match the current package identity and non-ownership rules
- downstream packages should still consume core rules instead of bypassing them

## Validation focus

- domain tests prove lifecycle transitions and invariant enforcement
- public-surface tests prove root imports and protocol contracts remain stable
- repository checks prove metadata, docs publication, and release wiring stay aligned

## Publication checkpoints

- package metadata, docs routes, and lifecycle-ownership language should match
  the current core contract before tagging
- release validation should leave lifecycle, validator, and public-surface
  proof green in the repository root check surface
- the published wheel and sdist should reflect the same canonical import root
  and package guide that maintainers reviewed locally

## Release escalation signals

- stop the release if a lifecycle change starts depending on runtime transport,
  provider, or CLI behavior to remain coherent
- escalate before tagging if the docs or exports blur core ownership with
  evidence, ranking, or lab-local semantics
- escalate when consumers would need silent import or protocol rewrites to keep
  ordinary lifecycle behavior working

## Release review questions

- does the release preserve canonical lifecycle, review-gate, or protocol
  behavior rather than drifting into a higher-layer policy surface
- would another package otherwise become the de facto owner of program
  semantics after this release
- can the release still be justified without borrowing evidence, ranking, lab,
  or runtime-delivery ownership

## Release checklist

1. Validate `README.md` and package docs describe current domain ownership.
2. Confirm `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
   still describe the same lifecycle and protocol ownership.
3. Run `make lint test quality security` from repository root.
4. Verify `.github/workflows/release-artifacts.yml` is configured for tag-triggered release (`v*`) with PyPI trusted publishing.
5. Create and push the release tag (`vX.Y.Z`) after changelog and metadata are final.
6. Confirm the release workflow uploaded and released both wheel and sdist artifacts.

## Explicit non-goals

- This page does not redefine lifecycle policy.
- This page does not replace public-surface or domain tests.
