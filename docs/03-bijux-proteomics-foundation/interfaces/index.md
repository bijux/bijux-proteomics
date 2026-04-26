---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Interfaces

This section shows which shared-contract surfaces are real promises: public
imports, schema definitions, serialized artifacts, migration helpers, and
examples that downstream packages can rely on safely.

These pages keep callers from hardening dependencies around incidental details.
For the foundation package, that matters because one sloppy contract
assumption can spread into every higher layer that consumes shared payloads or
identifiers.

## Visual Summary

```mermaid
flowchart LR
    imports["public imports"]
    schemas["schema contracts<br/>payload meaning"]
    serial["serialized artifacts<br/>and fingerprints"]
    migrate["migration helpers<br/>compatibility path"]
    examples["examples and operator use"]
    review["compatibility review<br/>what changes need extra care"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    imports --> schemas
    schemas --> serial
    schemas --> migrate
    serial --> examples
    migrate --> review
    class schemas page;
    class imports,serial,migrate positive;
    class examples anchor;
    class review action;
```

## Start Here

- open [Public Imports](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/public-imports/) when the dependency starts from
  Python entrypoints
- open [Data Contracts](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/data-contracts/) when the real question is payload
  shape, identity, or schema meaning
- open [Artifact Contracts](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/artifact-contracts/) when callers rely on
  serialized output or fingerprints
- open [Compatibility Commitments](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/compatibility-commitments/) when a change
  may break shared cross-package assumptions

## Published Interface Pages

- [CLI Surface](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/cli-surface/)
- [API Surface](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/api-surface/)
- [Configuration Surface](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/configuration-surface/)
- [Data Contracts](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/data-contracts/)
- [Artifact Contracts](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/artifact-contracts/)
- [Entrypoints and Examples](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/entrypoints-and-examples/)
- [Operator Workflows](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/operator-workflows/)
- [Public Imports](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/public-imports/)
- [Compatibility Commitments](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/interfaces/compatibility-commitments/)

## Open This Section When

- you need to know which shared-contract surface is intentional and supported
- downstream packages depend on schema meaning, identifiers, serialized output,
  or migration helpers
- you are reviewing whether a change creates compatibility pressure beyond one
  local package

## Open Another Section When

- the real question is why shared meaning belongs in this package at all
- you need structural layout or compatibility-helper organization first
- the issue is operational, such as validation workflow, release steps, or test
  execution

## Read Across The Package

- open [Foundation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/foundation/) when the contract issue is really a
  boundary or ownership question
- open [Architecture](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/) when the surface depends on
  schema, serialization, or migration structure
- open [Operations](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/operations/) when you need repeatable maintainer
  workflows for contract changes
- open [Quality](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/quality/) when the real question is whether the
  documented contract is sufficiently defended

## Concrete Anchors

- public exports in `src/bijux_proteomics_foundation/__init__.py`
- schema contracts in `src/bijux_proteomics_foundation/schema.py`
- serialization helpers in `src/bijux_proteomics_foundation/serialization.py`
- migration helpers in `src/bijux_proteomics_foundation/migrations.py`

## Reader Takeaway

Use `Interfaces` to separate stable shared contracts from whatever merely
happens to be visible in implementation today. If another package cannot defend
its dependency in terms of named imports, schemas, artifacts, examples, and
tests, that dependency is not yet an honest public surface.

## Purpose

This page shows the published interface routes for
`bijux-proteomics-foundation` and the supported surfaces that downstream
packages can rely on.
