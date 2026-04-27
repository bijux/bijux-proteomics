# PyPI Maintainer Notes

## Package identity

- package: `bijux-proteomics-runtime`
- import root: `bijux_proteomics_runtime`
- repository: `bijux/bijux-proteomics`
- owner: Bijan Mousavi (`bijan@bijux.io`)

## Release surface

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-runtime/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![Publish](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)

- package guide: <https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/>
- release and versioning: <https://bijux.io/bijux-proteomics/09-bijux-proteomics-runtime/operations/release-and-versioning/>
- package directory: <https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-runtime>
- verify workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml>
- release workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml>
- docs workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml>

## Release contract

- release must preserve canonical CLI, API, provider, and replay-safe execution
  behavior
- release docs must keep compat ownership separate from canonical runtime
  ownership
- downstream packages should continue to depend on runtime for operator-facing
  orchestration instead of rebuilding runtime semantics locally

## Validation focus

- runtime surface tests prove canonical entrypoints and replay boundaries stay
  stable
- migration tests prove compat forwarding still resolves to canonical runtime
  ownership
- repository release checks prove metadata, docs publication, and workflows stay
  aligned

## Publication checkpoints

- package metadata, docs routes, and canonical-runtime ownership language should
  match the current runtime contract before tagging
- release validation should leave runtime surface, migration, and provider proof
  green in the repository root check surface
- the published wheel and sdist should reflect the same canonical entrypoints
  and package guide that maintainers reviewed locally

## Release escalation signals

- stop the release if compat forwarding would need to invent behavior instead
  of mirroring canonical runtime ownership
- escalate before tagging if a CLI, API, provider, or replay change exposes a
  lower-package contract gap that runtime is trying to paper over
- escalate when the docs cannot explain entrypoint ownership without ambiguity
  between canonical runtime and compat surfaces

## Release checklist

1. Confirm `README.md` reflects current canonical runtime identity and entrypoint
   ownership.
2. Confirm `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
   still match current runtime authority, compat forwarding, and provider
   boundaries.
3. Run `make lint test quality security` from repository root.
4. Verify `.github/workflows/release-artifacts.yml` is configured for
   tag-triggered release (`v*`) with PyPI trusted publishing.
5. Create and push the release tag (`vX.Y.Z`) after changelog and metadata are
   final.
6. Confirm the release workflow uploaded and released both wheel and sdist
   artifacts.

## Explicit non-goals

- This page does not redefine compat migration policy.
- This page does not replace runtime surface, migration, or provider tests.
