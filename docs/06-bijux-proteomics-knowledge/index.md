---
title: bijux-proteomics-knowledge
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-knowledge

`bijux-proteomics-knowledge` is the evidence and claim package in
`bijux-proteomics`. Start here when the question is about evidence
quality, claim state transitions, contradiction resolution, trust
scoring, or readiness summaries consumed by downstream decision layers.

This section should make one promise clear: knowledge owns the recorded
evidence and claim state that readers can audit later. It is the place
to ask what is known, what conflicts, and how much trust the system can
currently justify.

## Visual Summary

```mermaid
flowchart LR
    records["evidence records"]
    claims["claim state and<br/>contradiction handling"]
    trust["freshness, confidence,<br/>and trust summaries"]
    knowledge["bijux-proteomics-knowledge<br/>auditable evidence layer"]
    intelligence["decision policy<br/>reads the evidence state"]
    runtime["runtime surfaces<br/>current evidence-backed status"]
    reviewers["reviewers can inspect<br/>why a claim is trusted"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    records --> knowledge
    claims --> knowledge
    trust --> knowledge
    knowledge --> intelligence
    knowledge --> runtime
    knowledge --> reviewers
    class knowledge page;
    class intelligence,runtime,reviewers positive;
    class records,claims,trust anchor;
```

## Read This Section When

- you need the package entrypoint for evidence and claim contracts
- you are checking contradiction handling, freshness, or trust logic
- you want the shortest route into auditable knowledge-state behavior

## Main Paths

- [Foundation](foundation/index.md)
- [Architecture](architecture/index.md)
- [Interfaces](interfaces/index.md)
- [Operations](operations/index.md)
- [Quality](quality/index.md)

## Cross-Package Handoffs

- move to [bijux-proteomics-intelligence](../05-bijux-proteomics-intelligence/index.md) when the question becomes ranking policy rather than evidence state
- move to [bijux-proteomics-lab](../07-bijux-proteomics-lab/index.md) when the concern becomes assay execution or planning
- stay here when the real issue is whether the current claim state is justified and inspectable

## Concrete Anchors

- `packages/bijux-proteomics-knowledge` for the package root
- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge` for evidence ownership
- `packages/bijux-proteomics-knowledge/tests` for contradiction and trust proof

## Purpose

This page gives readers the cleanest route into the package that owns
evidence state instead of merely consuming it.

## Stability

Keep it aligned with the evidence, claim, and trust behavior that the
package actually governs.
