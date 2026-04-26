---
title: Foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Foundation

`bijux-proteomics-foundation` exists to keep shared payload meaning stable
across the proteomics package family. Use this section when the important
question is not how a workflow runs, but why schemas, identifiers,
serialization, and migration helpers belong here in the first place.

These pages should help readers separate shared meaning from downstream policy.
When this section is doing its job well, a scientist or maintainer can explain
why higher packages may change workflow rules without changing what a payload,
identifier, or fingerprint means.

## Visual Summary

```mermaid
flowchart LR
    payloads["shared payload shapes"]
    ids["stable identifiers<br/>and migrations"]
    serial["deterministic serialization<br/>and fingerprints"]
    meaning["shared meaning layer"]
    boundary["boundary<br/>program policy starts later"]
    reader["reader question<br/>why is this shared across packages?"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    payloads --> meaning
    ids --> meaning
    serial --> meaning
    meaning --> boundary
    meaning --> reader
    class meaning page;
    class payloads,ids,serial positive;
    class reader anchor;
    class boundary caution;
```

## Start Here

- open [Package Overview](package-overview.md) for the shortest explanation of
  what the shared meaning layer owns
- open [Ownership Boundary](ownership-boundary.md) when the issue may actually
  belong in core, knowledge, intelligence, lab, or runtime
- open [Lifecycle Overview](lifecycle-overview.md) when the key question is how
  identifiers, payloads, and migrations stay stable over time

## Pages In This Section

- [Package Overview](package-overview.md)
- [Scope and Non-Goals](scope-and-non-goals.md)
- [Ownership Boundary](ownership-boundary.md)
- [Repository Fit](repository-fit.md)
- [Capability Map](capability-map.md)
- [Domain Language](domain-language.md)
- [Lifecycle Overview](lifecycle-overview.md)
- [Dependencies and Adjacencies](dependencies-and-adjacencies.md)
- [Change Principles](change-principles.md)

## Use This Section When

- you need the durable ownership story before reading code or compatibility
  details
- you are deciding whether a change affects shared payload meaning or only a
  downstream workflow
- you need the package vocabulary for schemas, fingerprints, identifiers, and
  migrations

## Do Not Use This Section When

- the question is already about public imports, schema contracts, or serialized
  artifacts
- the real issue is operational, such as setup, validation, or release
- you already know the boundary and need proof, risk posture, or review
  criteria instead

## Read Across The Package

- open [Architecture](../architecture/index.md) when you need the structural
  map behind schema, serialization, and migration code
- open [Interfaces](../interfaces/index.md) when the question is about imports,
  contracts, or compatibility promises
- open [Operations](../operations/index.md) when you need repeatable maintainer
  workflows for shared contract changes
- open [Quality](../quality/index.md) when you need evidence that the shared
  meaning layer is actually protected

## Concrete Anchors

- `packages/bijux-proteomics-foundation` as the package root
- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation` as the
  import boundary
- `packages/bijux-proteomics-foundation/tests` as the proof surface for shared
  contracts

## Reader Takeaway

Use `Foundation` to answer the ownership question with integrity:
`bijux-proteomics-foundation` exists so every downstream package can agree on
payload meaning before they disagree on policy. If a proposal broadens this
package without making that shared-meaning story clearer, it is probably
crossing the boundary rather than improving it.

## Purpose

This page introduces the foundation handbook for
`bijux-proteomics-foundation` and routes readers to the boundary, language, and
lifecycle pages that explain why the package exists.
