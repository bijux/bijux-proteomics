---
title: Integration Seams
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Integration Seams

Integration seams are the points where `bijux-proteomics-knowledge` meets configuration, APIs,
operators, or neighboring packages.

This page exists so integration changes do not feel mysterious. A reviewer should
be able to say which seams are intentional, which ones carry compatibility risk,
and where the package expects outside systems to meet it.

## Visual Summary

```mermaid
flowchart LR
    seam1["foundation payload seam"]
    seam2["intelligence policy seam"]
    seam3["runtime status seam"]
    page["bijux-proteomics-knowledge<br/>integration seams"]
    review1["caller expectations"]
    review2["contract alignment"]
    review3["drift checks"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    seam1 --> page
    seam2 --> page
    seam3 --> page
    page --> review1
    page --> review2
    page --> review3
    class page page;
    class seam1,seam2,seam3 anchor;
    class review1,review2,review3 action;
```

## Integration Surfaces

- ingestion adapters that normalize external inputs (`adapters.py`)
- serialization and schema boundaries used by other packages (`serialization.py`, `schema.py`)
- repository protocols and review summaries consumed by downstream decision layers (`repositories.py`, `review.py`)

## Adjacent Systems

- governs the other canonical packages instead of replacing their local ownership
- is the final authority for run acceptance, replay evaluation, and stored evidence

## Concrete Anchors

- `src/bijux_proteomics_knowledge/adapters.py`
- `src/bijux_proteomics_knowledge/evidence.py`
- `src/bijux_proteomics_knowledge/claims.py`
- `src/bijux_proteomics_knowledge/resolution.py`
- `src/bijux_proteomics_knowledge/review.py`

## Open This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Integration Seams` to decide whether a structural change makes `bijux-proteomics-knowledge` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

## What This Page Answers

- how `bijux-proteomics-knowledge` is organized internally in terms a reviewer can follow
- which modules carry the main execution and dependency story
- where structural drift would show up before it becomes expensive

## Reviewer Lens

- trace the described execution path through the named modules instead of trusting the diagram alone
- look for dependency direction or layering that now contradicts the documented seam
- verify that the structural risks named here still match the current code shape

## Honesty Boundary

This page describes the current structural model of `bijux-proteomics-knowledge`, but it does not guarantee that every import path or runtime path still obeys that model. Readers should treat it as a map that must stay aligned with code and tests, not as an authority above them.

## Next Checks

- open interfaces when the review reaches a public or operator-facing seam
- open operations when the concern becomes repeatable runtime behavior
- open quality when you need proof that the documented structure is still protected

## Purpose

This page shows where to look when integration behavior changes.

## Stability

Keep it aligned with real boundary modules and schema files.
