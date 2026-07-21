---
title: Testing and Validation
audience: contributor
type: reference
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-07-21
---

# Testing and validation

Validation is layered because different regressions require different proof.
Package tests establish local behavior. Contract, architecture, documentation,
security, build, and release gates establish that the repository still works as
one published product family.

## Validation ladder

```mermaid
flowchart LR
    focused["focused test"] --> package["package test and quality"]
    package --> contract["API and schema contracts"]
    contract --> boundary["dependency and architecture boundaries"]
    boundary --> repository["docs, security, build, SBOM"]
    repository --> release["release preflight"]
```

Run every layer whose governed surface changed; passing a broader command does
not make a skipped contract-specific check irrelevant.

## Change-to-check matrix

| Change | Minimum focused proof | Required broader proof |
| --- | --- | --- |
| package behavior | owning tests and affected invariants | package quality; root `make test` when shared |
| public Python API | public API tests | `make api`, `make quality-public-api-types` |
| JSON or OpenAPI contract | schema tests and representative round trip | `make api-freeze`, `make openapi-drift` |
| package dependency | import smoke test | `make quality-circular-imports`, dependency minimization and optional-dependency guards |
| runtime ownership or compatibility | targeted runtime tests | runtime boundary, migration-ledger, and migration-validation targets |
| documentation | example execution where applicable | link, consistency, and `make docs-check` |
| artifact location or generation | producing test or command | `make quality-artifact-governance` |
| release metadata or workflow | targeted workflow/config validation | `make release-preflight` |

## Core gates

```bash
make test-collection-gate
make test
make lint
make quality
make security
make api
make docs-check
```

The complete repository flow is:

```bash
make check
```

It runs lock validation, lint, collection, tests, quality, security,
documentation, API, builds, and SBOM generation. Results and logs belong below
`artifacts/`; a clean terminal alone is not the evidence when the target emits
a governed report.

## Architecture and runtime gates

Use the dedicated targets when a change touches ownership or execution seams:

```bash
make architecture-check
make quality-architecture-regression
make quality-runtime-boundaries
make quality-runtime-migration-ledger
make quality-runtime-migration-validation
```

These checks answer different questions. The boundary gate detects forbidden
ownership movement; the migration ledger checks coverage and freshness; the
migration validation suite exercises compatibility behavior.

## Documentation proof

Run examples against the installed workspace when they promise executable
behavior. Then validate the rendered site:

```bash
make quality-docs-links
make quality-docs-consistency
make docs-check
```

`docs-check` performs an isolated MkDocs build and checks documentation hygiene.
It should leave the root free of generated site directories.

## Interpreting failures

Do not silence a check or weaken a threshold to obtain a green run. Determine
whether the failure belongs to the change, an existing repository defect, the
environment, or generated drift. Record the exact command, failing package or
artifact, and diagnostic. A known failure remains a failure until its owning
surface is corrected.
