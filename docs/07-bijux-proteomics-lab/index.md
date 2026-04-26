---
title: bijux-proteomics-lab
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# bijux-proteomics-lab

`bijux-proteomics-lab` is the assay planning and outcomes package in
`bijux-proteomics`. Start here when the question is about experiment
batch design, dependency scheduling, rerun strategy, or closed-loop
transitions from assay observations into next-cycle planning.

Readers should come here to understand how recommended work becomes lab
work and how lab outcomes re-enter the system. This package is where the
abstract plan meets instrument-facing execution decisions and outcome
promotion.

## Visual Summary

```mermaid
flowchart LR
    candidates["candidate priorities<br/>and readiness inputs"]
    schedules["batch planning and<br/>dependency scheduling"]
    reruns["rerun and fallback<br/>strategy"]
    lab["bijux-proteomics-lab<br/>assay planning layer"]
    outcomes["assay outcomes<br/>and promotion decisions"]
    knowledge["knowledge captures<br/>new evidence"]
    runtime["runtime tracks<br/>execution and artifacts"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    candidates --> lab
    schedules --> lab
    reruns --> lab
    lab --> outcomes
    outcomes --> knowledge
    outcomes --> runtime
    class lab page;
    class outcomes,knowledge,runtime positive;
    class candidates,schedules,reruns anchor;
```

## Read This Section When

- you need the package entrypoint for planning and assay outcome docs
- you are checking scheduling, readiness, rerun, or promotion decisions
- you want the shortest route into closed-loop lab execution contracts

## Main Paths

- [Foundation](foundation/index.md)
- [Architecture](architecture/index.md)
- [Interfaces](interfaces/index.md)
- [Operations](operations/index.md)
- [Quality](quality/index.md)

## Cross-Package Handoffs

- move to [bijux-proteomics-intelligence](../05-bijux-proteomics-intelligence/index.md) when the unresolved question is recommendation policy
- move to [bijux-proteomics-knowledge](../06-bijux-proteomics-knowledge/index.md) when the unresolved question is evidence or contradiction state after an assay
- stay here when the real concern is how work is scheduled, rerun, or promoted after execution

## Concrete Anchors

- `packages/bijux-proteomics-lab` for the package root
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab` for planning and outcome ownership
- `packages/bijux-proteomics-lab/tests` for execution-planning proof

## Purpose

This page helps readers find the package where recommendations become
executable assay work and outcomes feed the next cycle.

## Stability

Keep it aligned with the planning, scheduling, rerun, and outcome logic
that the package actually owns.
