---
title: Package Map
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-docs
last_reviewed: 2026-04-10
---

# Package Map

The package map is the clearest explanation of the product idea in this
repository. Each package owns one distinct responsibility in the protein
program lifecycle.

```mermaid
flowchart TD
    Q[What kind of work is this?]
    Q --> R1[runtime / replay / execution]
    Q --> R2[schema / identifiers / serialization]
    Q --> R3[targets / gates / lifecycle]
    Q --> R4[ranking / scoring / recommendation]
    Q --> R5[evidence / claims / contradictions]
    Q --> R6[assay planning / outcomes / promotion]

    R1 --> P1[agentic-proteins]
    R2 --> P2[bijux-proteomics-foundation]
    R3 --> P3[bijux-proteomics-core]
    R4 --> P4[bijux-proteomics-intelligence]
    R5 --> P5[bijux-proteomics-knowledge]
    R6 --> P6[bijux-proteomics-lab]
```

## Canonical Package Roles

| Package | Core role | Open it when |
| --- | --- | --- |
| `agentic-proteins` | runtime orchestration, replay, and operator-facing execution | the question is about running, replaying, or governing execution |
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
