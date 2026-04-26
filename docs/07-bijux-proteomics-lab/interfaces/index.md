---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Interfaces

This section shows which imports, schemas, and artifacts
`bijux-proteomics-lab` is prepared to stand behind as real surfaces.

These pages show the public face of `bijux-proteomics-lab`. They help
a caller separate deliberate contracts from incidental visibility before
a dependency hardens around the wrong surface.

The important caller-facing question here is straightforward: which plan,
outcome, feedback, schema, and serialization surfaces are stable enough
to use without reading the whole package every time?

## Start Here

## Published Interface Pages

- [CLI Surface](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/cli-surface/)
- [API Surface](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/api-surface/)
- [Configuration Surface](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/configuration-surface/)
- [Data Contracts](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/data-contracts/)
- [Artifact Contracts](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/artifact-contracts/)
- [Entrypoints and Examples](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/entrypoints-and-examples/)
- [Operator Workflows](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/operator-workflows/)
- [Public Imports](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/public-imports/)
- [Compatibility Commitments](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/compatibility-commitments/)

## What This Section Clarifies

- which Python exports in `bijux_proteomics_lab` are meant to be stable public
  entrypoints
- which artifact kinds and schema rules callers must preserve when they store
  or exchange lab outputs
- which serialization helpers exist to keep payloads deterministic and auditable

## Open This Section When

- you need the public import, schema, or artifact surface
- you are checking whether a caller can safely rely on a given entrypoint or shape
- you want the contract-facing side of the package before building on it

## Open Another Section When

- the real question is whether the package should own the behavior at all
- the real question is how the internal files are arranged
- the real question is which workflow a maintainer should run during planning or
  outcome review

## Read Across the Package

- [Foundation](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/) when you need the package boundary first
- [Architecture](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/) when a public-surface question turns
  into a module-ownership question
- [Operations](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/operations/) when the interface question becomes a
  repeatable maintainer workflow
- [Quality](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/quality/) when the real concern is compatibility proof
  and review sufficiency

## Concrete Anchors

- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/__init__.py`
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/planning.py`
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/outcomes.py`
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/schema.py`
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/serialization.py`
- `packages/bijux-proteomics-lab/tests/test_schema.py` and
  `packages/bijux-proteomics-lab/tests/test_serialization.py`

## Bottom Line

Use the interfaces section when you need to know what a caller may trust
without treating every importable symbol as public. If a surface cannot be tied
to a named export, artifact contract, or deterministic serialization rule, it
should not be treated as stable.
