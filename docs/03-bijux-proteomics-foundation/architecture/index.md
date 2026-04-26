---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-26
---

# Architecture

`bijux-proteomics-foundation` architecture should answer one structural question quickly: where the owned behavior lives, how it flows, and which seams must stay visible so the package does not absorb package-specific domain policy or workflow logic.

## Start With

- open [Module Map](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/module-map/) when you need the fastest route from filenames to owned module families
- open [Execution Model](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/execution-model/) when the question is how shared payload meaning moves through ids, schemas, serialization, and migration helpers without picking up policy
- open [Integration Seams](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/integration-seams/) when a change may cross into package-specific domain policy or workflow logic

## Section Pages

- [Module Map](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/module-map/)
- [Dependency Direction](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/dependency-direction/)
- [Execution Model](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/execution-model/)
- [State and Persistence](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/state-and-persistence/)
- [Integration Seams](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/integration-seams/)
- [Error Model](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/error-model/)
- [Extensibility Model](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/extensibility-model/)
- [Code Navigation](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/code-navigation/)
- [Architecture Risks](https://bijux.io/bijux-proteomics/03-bijux-proteomics-foundation/architecture/architecture-risks/)

## First Proof Check

- `src/bijux_proteomics_foundation/ids.py` and `schema.py` for stable shared meaning
- `src/bijux_proteomics_foundation/serialization.py` and `migrations.py` for transport and compatibility structure
- `src/bijux_proteomics_foundation/errors.py` for shared failure vocabulary

## Boundary Test

If a reviewer cannot name the owning module family before touching code, the package structure is still too implicit.
