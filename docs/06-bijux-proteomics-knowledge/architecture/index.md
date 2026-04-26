---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Architecture

`bijux-proteomics-knowledge` architecture should answer one structural question quickly: where the owned behavior lives, how it flows, and which seams must stay visible so the package does not absorb recommendation policy or runtime storage concerns.

## Start With

- open [Module Map](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/module-map/) when you need the fastest route from filenames to owned module families
- open [Execution Model](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/execution-model/) when the question is how evidence enters through claim and graph structures, then moves through confidence and resolution paths into reviewable outputs
- open [Integration Seams](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/integration-seams/) when a change may cross into recommendation policy or runtime storage concerns

## Section Pages

- [Module Map](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/module-map/)
- [Dependency Direction](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/dependency-direction/)
- [Execution Model](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/execution-model/)
- [State and Persistence](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/state-and-persistence/)
- [Integration Seams](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/integration-seams/)
- [Error Model](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/error-model/)
- [Extensibility Model](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/extensibility-model/)
- [Code Navigation](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/code-navigation/)
- [Architecture Risks](https://bijux.io/bijux-proteomics/06-bijux-proteomics-knowledge/architecture/architecture-risks/)

## First Proof Check

- `src/bijux_proteomics_knowledge/claims.py`, `evidence.py`, and `graph.py` for canonical knowledge structures
- `src/bijux_proteomics_knowledge/confidence/segments.py`, `resolution.py`, and `review.py` for trust and contradiction handling
- `src/bijux_proteomics_knowledge/repositories.py`, `schema.py`, and `serialization.py` for durable boundaries

## Boundary Test

If a reviewer cannot name the owning module family before touching code, the package structure is still too implicit.
