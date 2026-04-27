# PyPI Maintainer Notes

## Package identity

- package: `bijux-proteomics-lab`
- import root: `bijux_proteomics_lab`
- repository: `bijux/bijux-proteomics`
- owner: Bijan Mousavi (`bijan@bijux.io`)

## Release surface

[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-3776AB?logo=python&logoColor=white)](https://pypi.org/project/bijux-proteomics-lab/)
[![License: Apache-2.0](https://img.shields.io/badge/license-Apache--2.0-0F766E)](https://github.com/bijux/bijux-proteomics/blob/main/LICENSE)
[![Verify](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml)
[![Publish](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml)
[![Docs](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml)

- package guide: <https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/>
- release and versioning: <https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/operations/release-and-versioning/>
- package directory: <https://github.com/bijux/bijux-proteomics/tree/main/packages/bijux-proteomics-lab>
- verify workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/verify.yml>
- release workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/release-github.yml>
- docs workflow: <https://github.com/bijux/bijux-proteomics/actions/workflows/deploy-docs.yml>

## Release contract

- release must preserve planning, outcome, and feedback semantics without
  pulling lifecycle or evidence truth ownership into the lab layer
- release docs must match the current planning and outcome boundary
- downstream packages should still rely on this layer for lab execution logic

## Validation focus

- planning and outcome tests prove batch, rerun, and promotion behavior
- repository tests prove feedback/repository contracts remain stable
- repository release checks prove metadata, docs publication, and workflows stay aligned

## Publication checkpoints

- package metadata, docs routes, and planning-ownership language should match
  the current lab contract before tagging
- release validation should leave planning, outcome, repository, and schema
  proof green in the repository root check surface
- the published wheel and sdist should reflect the same import root and package
  guide that maintainers reviewed locally

## Release escalation signals

- stop the release if planning or rerun behavior now depends on runtime
  transport internals or on knowledge truth rewrites to remain coherent
- escalate before tagging if the docs start treating lifecycle, ranking, or
  evidence semantics as lab-owned behavior
- escalate when outcome or repository changes cannot be justified by focused
  lab proof without widening another package boundary

## Release review questions

- does the release preserve planning, batching, rerun guidance, or outcome
  promotion meaning rather than only changing how those results are exposed
- would runtime or intelligence code otherwise start carrying shadow scheduling
  or rerun contracts after this release
- can the release still be justified without claiming lifecycle, evidence,
  ranking, or provider-interface ownership

## Release impact signals

- expect downstream review when planning, batching, rerun, or outcome-promotion
  semantics change because operator workflows depend on them staying stable
- treat changes that alter scheduling behavior, rerun decisions, or outcome
  meaning as high-impact even when import roots and public names stay stable
- expect a narrower release burden when the change only improves internal
  implementation without changing lab execution semantics

## Release communication signals

- call out planning, rerun, or outcome-promotion changes explicitly when
  operators may need to adjust workflow expectations after the release
- name scheduling or batching behavior shifts directly instead of hiding them
  inside generic maintenance wording
- keep release messaging brief when the change only improves internals without
  changing lab execution semantics

## Release checklist

1. Validate README and docs reflect current planning and outcome contracts.
2. Confirm `docs/BOUNDARIES.md`, `docs/CONTRACTS.md`, and `docs/ARCHITECTURE.md`
   still describe the same planning and outcome ownership.
3. Run `make lint test quality security` from repository root.
4. Verify `.github/workflows/release-artifacts.yml` is configured for tag-triggered release (`v*`) with PyPI trusted publishing.
5. Create and push the release tag (`vX.Y.Z`) after changelog and metadata are final.
6. Confirm the release workflow uploaded and released both wheel and sdist artifacts.

## Explicit non-goals

- This page does not redefine planning or rerun policy.
- This page does not replace planning, outcome, or schema tests.
