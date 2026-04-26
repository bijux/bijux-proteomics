---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Architecture

`bijux-proteomics-intelligence` architecture should answer one structural question quickly: where the owned behavior lives, how it flows, and which seams must stay visible so the package does not absorb knowledge-evidence semantics or lab execution decisions.

## Start With

- open [Module Map](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/module-map/) when you need the fastest route from filenames to owned module families
- open [Execution Model](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/execution-model/) when the question is how candidate inputs move through policies and evaluators into reports and reviewed outcomes
- open [Integration Seams](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/integration-seams/) when a change may cross into knowledge-evidence semantics or lab execution decisions

## Section Pages

- [Module Map](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/module-map/)
- [Dependency Direction](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/dependency-direction/)
- [Execution Model](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/execution-model/)
- [State and Persistence](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/state-and-persistence/)
- [Integration Seams](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/integration-seams/)
- [Error Model](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/error-model/)
- [Extensibility Model](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/extensibility-model/)
- [Code Navigation](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/code-navigation/)
- [Architecture Risks](https://bijux.io/bijux-proteomics/05-bijux-proteomics-intelligence/architecture/architecture-risks/)

## First Proof Check

- `src/bijux_proteomics_intelligence/candidates.py` and `domain/candidates/` for decision inputs
- `src/bijux_proteomics_intelligence/policies.py`, `evaluators.py`, and `domain/metrics/` for scoring structure
- `src/bijux_proteomics_intelligence/report/`, `briefs.py`, `outcomes.py`, and `design_loop/` for explainability and control

## Boundary Test

If a reviewer cannot name the owning module family before touching code, the package structure is still too implicit.
