---
title: agentic-proteins
audience: mixed
type: index
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# agentic-proteins

`agentic-proteins` is the strict compatibility package in
`bijux-proteomics`. Its job is to preserve legacy import paths and CLI
entrypoints long enough for callers to move safely to
`bijux-proteomics-runtime`.

Treat this package as a bridge, not as the center of new development.
Readers should leave this section knowing which compatibility surface is
still preserved, where the canonical runtime now lives, and what proof
should exist before the bridge is kept or removed.

## Visual Summary

```mermaid
flowchart LR
    legacyImport["legacy imports and scripts"]
    legacyCli["legacy CLI entrypoints"]
    compat["agentic-proteins<br/>compatibility layer"]
    runtime["bijux-proteomics-runtime<br/>canonical runtime authority"]
    contracts["compatibility commitments<br/>and forwarding rules"]
    migration["migration-safe handoff<br/>to runtime docs and code"]
    newWork["new runtime work<br/>belongs in runtime"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    legacyImport --> compat
    legacyCli --> compat
    compat --> runtime
    compat --> contracts
    contracts --> migration
    runtime --> newWork
    class compat page;
    class runtime positive;
    class legacyImport,legacyCli caution;
    class contracts,migration anchor;
    class newWork action;
```

## Read This Section When

- you need compatibility-safe legacy import or CLI entrypoints
- you are validating forwarding boundaries and migration promises
- you need to trace older runtime usage to the canonical runtime package

## Main Paths

- [Foundation](foundation/index.md)
- [Architecture](architecture/index.md)
- [Interfaces](interfaces/index.md)
- [Operations](operations/index.md)
- [Quality](quality/index.md)

## Cross-Package Handoffs

- move to [bijux-proteomics-runtime](../09-bijux-proteomics-runtime/index.md) when the question is about current runtime behavior
- move to [Repository Handbook](../01-bijux-proteomics/index.md) when the question is about migration policy or repository-wide release rules
- stay here only while the question is about preserved legacy surfaces and their retirement bar

## Concrete Anchors

- `packages/agentic-proteins` for the compatibility package root
- `packages/agentic-proteins/src/agentic_proteins` for preserved imports
- `packages/agentic-proteins/tests` for forwarding and compatibility proof

## Purpose

This page gives readers an honest starting point for the legacy bridge
package without implying that the bridge is the long-term destination.

## Stability

Keep it aligned with the preserved import and CLI surfaces that still
ship from `packages/agentic-proteins`.
