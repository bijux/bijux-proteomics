---
title: Package Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-26
---

# Package Map

The package map is the clearest explanation of the product idea in this
repository. Each package owns one distinct responsibility in the protein
program lifecycle.

```mermaid
flowchart TD
    question["what kind of work is this?"]
    runtime["runtime, replay, execution"]
    foundation["schema, identifiers, serialization"]
    core["programs, gates, lifecycle"]
    intelligence["ranking, scoring, recommendations"]
    knowledge["evidence, claims, contradictions"]
    lab["assay planning, outcomes, promotion"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    question --> runtime
    question --> foundation
    question --> core
    question --> intelligence
    question --> knowledge
    question --> lab
    class question page;
    class runtime,foundation,core,intelligence,knowledge,lab positive;
```

## Canonical Package Roles

| Package | Core role | Open it when |
| --- | --- | --- |
| `bijux-proteomics-runtime` | canonical runtime orchestration, replay, and operator-facing execution | the question is about running, replaying, or governing execution |
| `agentic-proteins` | compatibility package for existing runtime imports and entrypoints | the work is preserving legacy runtime paths during migration |
| `bijux-proteomics-foundation` | shared schema compatibility and canonical serialization primitives | the issue spans payload meaning, identifiers, or migration helpers |
| `bijux-proteomics-core` | program models, lifecycle contracts, and gate semantics | you are changing target, gate, or program-state behavior |
| `bijux-proteomics-intelligence` | candidate scoring, ranking policy, and decision support | you are tuning recommendation logic or explainability |
| `bijux-proteomics-knowledge` | evidence graphs, claims, and contradiction handling | the work concerns evidence trust or knowledge consistency |
| `bijux-proteomics-lab` | assay planning, outcomes, and closed-loop lab decisions | the question concerns experiment execution or outcome promotion |

## Shared Non-Product Surfaces

- [bijux-proteomics-maintain](../../08-bijux-proteomics-maintain/index.md) for
  repository-health automation and maintainer docs

## Purpose

This page helps readers choose the owning package before they start diffing the
whole repository.

## Stability

Keep it aligned with the packages that still ship from this repository and the
roles they actually own.
