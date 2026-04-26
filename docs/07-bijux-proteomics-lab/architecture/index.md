---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Architecture

`bijux-proteomics-lab` architecture should answer one structural question quickly: where the owned behavior lives, how it flows, and which seams must stay visible so the package does not absorb intelligence recommendation logic or shared foundation meaning.

## Start With

- open [Module Map](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/module-map/) when you need the fastest route from filenames to owned module families
- open [Execution Model](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/execution-model/) when the question is how recommended work becomes assay planning and outcome updates without importing decision policy into the lab package
- open [Integration Seams](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/integration-seams/) when a change may cross into intelligence recommendation logic or shared foundation meaning

## Section Pages

- [Module Map](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/module-map/)
- [Dependency Direction](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/dependency-direction/)
- [Execution Model](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/execution-model/)
- [State and Persistence](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/state-and-persistence/)
- [Integration Seams](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/integration-seams/)
- [Error Model](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/error-model/)
- [Extensibility Model](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/extensibility-model/)
- [Code Navigation](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/code-navigation/)
- [Architecture Risks](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/architecture-risks/)

## First Proof Check

- `src/bijux_proteomics_lab/planning.py` and `outcomes.py` for the lab-facing control flow
- `src/bijux_proteomics_lab/schema.py` and `serialization.py` for contract structure
- `src/bijux_proteomics_lab/repositories.py` for durable storage boundaries

## Boundary Test

If a reviewer cannot name the owning module family before touching code, the package structure is still too implicit.
