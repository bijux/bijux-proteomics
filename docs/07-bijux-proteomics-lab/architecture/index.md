---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Architecture

This section explains how `bijux_proteomics_lab` is organized so a
reviewer can follow structure, dependency direction, and execution flow
without guessing.

These pages should turn `bijux-proteomics-lab` from a directory listing
into a readable design map. Use them when a structural change needs to
be grounded in named modules and real execution paths.

The architectural story here is compact on purpose. The package is small
enough that the main question is not "which layer among twenty?" but
"which file owns planning, which file owns outcomes, and where are the
contracts that keep the loop deterministic?"

## Pages In This Section

- [Module Map](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/module-map/)
- [Dependency Direction](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/dependency-direction/)
- [Execution Model](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/execution-model/)
- [State and Persistence](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/state-and-persistence/)
- [Integration Seams](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/integration-seams/)
- [Error Model](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/error-model/)
- [Extensibility Model](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/extensibility-model/)
- [Code Navigation](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/code-navigation/)
- [Architecture Risks](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/architecture/architecture-risks/)

## What This Section Clarifies

- which source files carry the main planning, outcome, persistence, and
  contract responsibilities
- how the closed loop moves from plan construction to observed outcome and back
  into feedback
- where structural drift would show up first if ownership starts bleeding
  across files

## Open This Section When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Open Another Section When

- the real question is whether the package should own the behavior at all
- the real question is which import, schema, or artifact contract callers may
  depend on
- the real question is whether the current structure is sufficiently tested

## Read Across the Package

- [Foundation](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/foundation/) when you need the package boundary and
  ownership story first
- [Interfaces](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/interfaces/) when the question becomes what a caller
  can rely on
- [Operations](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/operations/) when the question becomes how maintainers
  repeat planning and outcome workflows
- [Quality](https://bijux.io/bijux-proteomics/07-bijux-proteomics-lab/quality/) when the question becomes whether structural
  claims still have enough proof behind them

## Concrete Anchors

- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/planning.py`
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/outcomes.py`
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/repositories.py`
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/schema.py`
- `packages/bijux-proteomics-lab/src/bijux_proteomics_lab/serialization.py`

## Bottom Line

Use the architecture section when you need a file-level map of the lab loop.
If a change makes it harder to explain why one of these files owns its current
responsibility, the design is drifting even if the code still passes.
