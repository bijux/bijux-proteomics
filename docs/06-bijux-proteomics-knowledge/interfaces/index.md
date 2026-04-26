---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Interfaces

Use this section when the question is what another package, tool, or reviewer
can safely rely on from `bijux-proteomics-knowledge`: import surfaces, schema
profiles, canonical JSON behavior, evidence bundles, claim records, and review
artifacts.

This package is library-first, but that does not make its contracts casual.
When evidence and claim state move across package boundaries, import surfaces
and serialized payloads become part of the review surface that later decisions
depend on.

## Visual Summary

```mermaid
flowchart LR
    imports["public imports and exported models"]
    schemas["schema compatibility and payload profiles"]
    serialization["canonical JSON and serialization rules"]
    artifacts["evidence bundles, claims, and review artifacts"]
    reader["reader question<br/>which knowledge surfaces are real contracts?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    class imports,page reader;
    class schemas,serialization positive;
    class artifacts anchor;
    imports --> reader
    schemas --> reader
    serialization --> reader
    artifacts --> reader
```

## Start Here

- open [Public Imports](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/public-imports/) for the package exports that callers
  should depend on directly
- open [Data Contracts](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/data-contracts/) and [Artifact Contracts](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/artifact-contracts/)
  when the durable payload or review shape matters more than the import name
- open [Configuration Surface](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/configuration-surface/) when the question is
  schema profile behavior rather than record semantics

## Published Interface Pages

- [CLI Surface](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/cli-surface/)
- [API Surface](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/api-surface/)
- [Configuration Surface](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/configuration-surface/)
- [Data Contracts](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/data-contracts/)
- [Artifact Contracts](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/artifact-contracts/)
- [Entrypoints and Examples](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/entrypoints-and-examples/)
- [Operator Workflows](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/operator-workflows/)
- [Public Imports](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/public-imports/)
- [Compatibility Commitments](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/interfaces/compatibility-commitments/)

## Open This Section When

- you need to know whether an import, schema, payload, or artifact shape is
  meant to be stable
- a change may affect downstream trust calculations, review packets, or bundle
  serialization
- a reviewer needs to separate explicit contracts from incidental visibility

## Open Another Section When

- the main question is why the behavior belongs in the knowledge layer at all
- the concern is mostly structural rather than contract-facing
- the issue is procedural or proof-oriented rather than about supported surfaces

## Read Across The Package

- open [Foundation](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/foundation/) for package purpose and ownership
- open [Architecture](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/) for the structural seams behind
  the public surfaces
- open [Operations](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/operations/) for workflows, diagnostics, and
  release procedures
- open [Quality](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/quality/) for compatibility evidence and review
  pressure

## Concrete Anchors

- `src/bijux_proteomics_knowledge/__init__.py` for public import exports
- `src/bijux_proteomics_knowledge/schema.py` for schema compatibility contracts
- `src/bijux_proteomics_knowledge/serialization.py` for canonical serialization rules
- `src/bijux_proteomics_knowledge/evidence.py` and `claims.py` for core data surfaces

## Reader Takeaway

Use `Interfaces` to judge whether a dependency on knowledge state is
defensible. The bar is that imports, schema profiles, serialized payloads,
artifacts, examples, and tests all agree about what a caller may rely on.

## What You Get

This page shows the published interface routes through
`bijux-proteomics-knowledge` before you inspect a specific contract surface.
