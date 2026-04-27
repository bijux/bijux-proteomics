# PyPI Maintainer Notes

## Package identity

- package: `bijux-proteomics-intelligence`
- import root: `bijux_proteomics_intelligence`
- repository: `bijux/bijux-proteomics`
- owner: Bijan Mousavi (`bijan@bijux.io`)

## Release surface

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-intelligence/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![Publish](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)

- package guide: <https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/>
- release and versioning: <https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/operations/release-and-versioning/>
- package directory: <https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-intelligence>
- verify workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml>
- release workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml>
- docs workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml>

## Release contract

- release must preserve reproducible ranking and scenario policy behavior
- release docs must match current ownership boundaries and canonical public roots
- downstream packages should still depend on this layer for recommendation logic

## Validation focus

- ranking and evaluator tests prove deterministic policy behavior
- public package docs prove recommendation ownership and non-ownership stay clear
- repository release checks prove package metadata and workflows remain aligned

## Publication checkpoints

- package metadata, docs routes, and recommendation-ownership language should
  match the current policy contract before tagging
- release validation should leave ranking, evaluator, and public-surface proof
  green in the repository root check surface
- the published wheel and sdist should reflect the same import root and package
  guide that maintainers reviewed locally

## Release escalation signals

- stop the release if ranking or explainability behavior now depends on runtime
  delivery details or lab-local orchestration to stay meaningful
- escalate before tagging if the docs start treating evidence truth or
  canonical execution as intelligence-owned behavior
- escalate when downstream consumers would need quiet policy-output rewrites to
  preserve recommendation semantics

## Release checklist

1. Verify README and package docs describe current ranking/scenario behavior.
2. Confirm `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
   still describe the same policy and recommendation ownership.
3. Run `make lint test quality security` from repository root.
4. Verify `.github/workflows/release-artifacts.yml` is configured for tag-triggered release (`v*`) with PyPI trusted publishing.
5. Create and push the release tag (`vX.Y.Z`) after changelog and metadata are final.
6. Confirm the release workflow uploaded and released both wheel and sdist artifacts.

## Explicit non-goals

- This page does not redefine ranking policy semantics.
- This page does not replace evaluator and scenario tests.
