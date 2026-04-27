# PyPI Maintainer Notes

## Package identity

- package: `agentic-proteins`
- import root: `agentic_proteins`
- repository: `bijux/bijux-proteomics`
- owner: Bijan Mousavi (`bijan@bijux.io`)

## Release surface

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/agentic-proteins/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![Publish](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)

- package guide: <https://bijux.io/bijux-proteomics/02-agentic-proteins/>
- release and versioning: <https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/release-and-versioning/>
- package directory: <https://github.com/bijux/bijux-proteomics/tree/main/packages/agentic-proteins>
- verify workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml>
- release workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml>
- docs workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml>

## Release contract

- release must preserve compatibility routing without reclaiming canonical
  runtime or domain ownership
- release docs must name `bijux-proteomics-runtime` as the canonical runtime
  owner for forwarded execution behavior
- downstream consumers should still be able to migrate from legacy imports
  without behavioral ambiguity

## Validation focus

- forwarding tests prove legacy imports and entrypoints still resolve to
  canonical packages
- migration tests prove compat metadata still matches canonical ownership
- repository release checks prove metadata, docs publication, and workflows stay
  aligned

## Publication checkpoints

- package metadata, docs routes, and compat-only ownership language should
  match the current forwarding contract before tagging
- release validation should leave forwarding, migration, and release-proof
  checks green in the repository root check surface
- the published wheel and sdist should reflect the same legacy package identity
  and canonical replacement guidance that maintainers reviewed locally

## Release escalation signals

- stop the release if the compat package adds new product behavior instead of
  forwarding canonical package behavior
- escalate before tagging if the docs stop naming `bijux-proteomics-runtime` or
  the lower canonical package as the true owner of forwarded behavior
- escalate when migration proof no longer shows a single unambiguous path from
  legacy imports to canonical ownership

## Release checklist

1. Verify `README.md` and package docs reflect current compat-only ownership.
2. Confirm `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
   still describe compatibility routing instead of canonical runtime authority.
3. Run `make lint test quality security` from repository root.
4. Verify `.github/workflows/release-artifacts.yml` is configured for tag-triggered release (`v*`) with PyPI trusted publishing.
5. Create and push the release tag (`vX.Y.Z`) after changelog and metadata are final.
6. Confirm the release workflow uploaded and released both wheel and sdist artifacts.

## Explicit non-goals

- This page does not redefine canonical runtime behavior.
- This page does not replace forwarding, migration, or release workflow tests.
