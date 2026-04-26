---
title: bijux-proteomics-foundation
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-foundation

`bijux-proteomics-foundation` is the shared schema and serialization
package in `bijux-proteomics`. Start here when the question is about
canonical payload shape, version compatibility helpers, identity
primitives, or deterministic serialization contracts used across the
package family.

Readers should come away from this section with one clear idea: this
package stabilizes shared meaning so the higher packages can disagree
about policy or workflow without disagreeing about what a payload is.

## Visual Summary

```mermaid
flowchart LR
    schema["schema profiles"]
    serialization["canonical serialization<br/>and fingerprints"]
    identifiers["stable identifiers<br/>and migration helpers"]
    foundation["bijux-proteomics-foundation<br/>shared meaning layer"]
    core["core contracts"]
    knowledge["knowledge state"]
    intelligence["decision logic"]
    lab["lab planning"]
    runtime["runtime orchestration"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    schema --> foundation
    serialization --> foundation
    identifiers --> foundation
    foundation --> core
    foundation --> knowledge
    foundation --> intelligence
    foundation --> lab
    foundation --> runtime
    class foundation page;
    class core,knowledge,intelligence,lab,runtime positive;
    class schema,serialization,identifiers anchor;
```

## Read This Section When

- you need the package entrypoint for schema and payload contracts
- you are checking identifiers, migrations, or serialization guarantees
- you want the shortest route into shared cross-package primitives

## Main Paths

- [Foundation](foundation/index.md)
- [Architecture](architecture/index.md)
- [Interfaces](interfaces/index.md)
- [Operations](operations/index.md)
- [Quality](quality/index.md)

## Cross-Package Handoffs

- move to [bijux-proteomics-core](../04-bijux-proteomics-core/index.md) when the concern becomes program or lifecycle behavior
- move to [bijux-proteomics-runtime](../09-bijux-proteomics-runtime/index.md) when the concern becomes execution or replay
- stay here when the real question is whether shared payload meaning changed

## Concrete Anchors

- `packages/bijux-proteomics-foundation` for the package root
- `packages/bijux-proteomics-foundation/src/bijux_proteomics_foundation` for canonical primitives
- `packages/bijux-proteomics-foundation/tests` for compatibility proof

## Purpose

This page helps readers locate the shared meaning layer before they dive
into downstream policy or workflow packages.

## Stability

Keep it aligned with the payload, identifier, and serialization contracts
that multiple packages rely on.
