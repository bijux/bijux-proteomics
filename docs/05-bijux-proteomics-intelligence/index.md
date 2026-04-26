---
title: bijux-proteomics-intelligence
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-intelligence

`bijux-proteomics-intelligence` is the decision and ranking package in
`bijux-proteomics`. Start here when the question is about candidate
scoring, portfolio ordering, scenario evaluation, or explainability
outputs used to advance or redesign programs.

Readers should use this section to distinguish decision policy from the
lower-layer contracts it depends on. Intelligence turns evidence and
program constraints into inspectable recommendations; it does not define
the shared payload model or the execution machinery itself.

## Visual Summary

```mermaid
flowchart LR
    evidence["knowledge evidence<br/>and trust signals"]
    constraints["core gates and<br/>lifecycle constraints"]
    scenarios["candidate and scenario<br/>comparison inputs"]
    intelligence["bijux-proteomics-intelligence<br/>decision policy layer"]
    explain["rankings and explanations"]
    lab["lab planning choices"]
    runtime["runtime orchestration<br/>uses the chosen path"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    evidence --> intelligence
    constraints --> intelligence
    scenarios --> intelligence
    intelligence --> explain
    explain --> lab
    explain --> runtime
    class intelligence page;
    class explain,lab,runtime positive;
    class evidence,constraints,scenarios anchor;
```

## Read This Section When

- you need the package entrypoint for scoring and recommendation logic
- you are checking ranking policy, scenario evaluation, or explanation outputs
- you want the shortest route into inspectable decision behavior

## Main Paths

- [Foundation](foundation/index.md)
- [Architecture](architecture/index.md)
- [Interfaces](interfaces/index.md)
- [Operations](operations/index.md)
- [Quality](quality/index.md)

## Cross-Package Handoffs

- move to [bijux-proteomics-knowledge](../06-bijux-proteomics-knowledge/index.md) when the real disagreement is about evidence or trust state
- move to [bijux-proteomics-core](../04-bijux-proteomics-core/index.md) when the rule belongs in a durable contract rather than a ranking policy
- stay here when you need to understand why one candidate or path was recommended over another

## Concrete Anchors

- `packages/bijux-proteomics-intelligence` for the package root
- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence` for decision logic ownership
- `packages/bijux-proteomics-intelligence/tests` for recommendation proof

## Purpose

This page helps readers locate the package that explains recommendations
instead of just consuming them.

## Stability

Keep it aligned with the decision, ranking, and explainability behavior
that the package actually owns.
