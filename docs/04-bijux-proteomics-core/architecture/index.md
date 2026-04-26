---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Architecture

`bijux-proteomics-core` architecture should answer one structural question quickly: where the owned behavior lives, how it flows, and which seams must stay visible so the package does not absorb runtime orchestration or recommendation policy.

## Start With

- open [Module Map](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/module-map/) when you need the fastest route from filenames to owned module families
- open [Execution Model](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/execution-model/) when the question is how program definitions and readiness rules move through contract modules without collapsing into runtime orchestration
- open [Integration Seams](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/integration-seams/) when a change may cross into runtime orchestration or recommendation policy

## Section Pages

- [Module Map](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/module-map/)
- [Dependency Direction](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/dependency-direction/)
- [Execution Model](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/execution-model/)
- [State and Persistence](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/state-and-persistence/)
- [Integration Seams](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/integration-seams/)
- [Error Model](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/error-model/)
- [Extensibility Model](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/extensibility-model/)
- [Code Navigation](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/code-navigation/)
- [Architecture Risks](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/architecture-risks/)

## First Proof Check

- `src/bijux_proteomics/program_spec.py`, `programs.py`, and `targets.py` for durable contracts
- `src/bijux_proteomics/lifecycle.py`, `validation.py`, and `execution_contracts.py` for readiness and execution rules
- `src/bijux_proteomics/biology/`, `domain/`, and `runtime_adapter.py` for structural seams to neighboring concerns

## Boundary Test

If a reviewer cannot name the owning module family before touching code, the package structure is still too implicit.
