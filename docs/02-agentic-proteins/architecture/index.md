---
title: Architecture
audience: mixed
type: index
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Architecture

`agentic-proteins` architecture should answer one structural question quickly: where the owned behavior lives, how it flows, and which seams must stay visible so the package does not absorb runtime ownership or lower-package scientific meaning.

## Start With

- open [Module Map](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/module-map/) when you need the fastest route from filenames to owned module families
- open [Execution Model](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/execution-model/) when the question is how a legacy import, CLI call, or API request flows through compatibility modules and reaches the canonical runtime seam
- open [Integration Seams](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/integration-seams/) when a change may cross into runtime ownership or lower-package scientific meaning

## Section Pages

- [Module Map](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/module-map/)
- [Dependency Direction](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/dependency-direction/)
- [Execution Model](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/execution-model/)
- [State and Persistence](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/state-and-persistence/)
- [Integration Seams](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/integration-seams/)
- [Error Model](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/error-model/)
- [Extensibility Model](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/extensibility-model/)
- [Code Navigation](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/code-navigation/)
- [Architecture Risks](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/architecture-risks/)

## First Proof Check

- `src/agentic_proteins/interfaces/`, `api/`, and `runtime/` for the public-to-runtime path
- `src/agentic_proteins/core/`, `execution/`, and `validation/` for legacy control logic
- `src/agentic_proteins/providers/`, `memory/`, and `report/` for remaining adapter and artifact seams

## Boundary Test

If a reviewer cannot name the owning module family before touching code, the package structure is still too implicit.
