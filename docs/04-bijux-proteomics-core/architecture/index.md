---
title: Architecture
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Architecture

Use this section when the important question is how the core contract layer is
organized: where program models live, how lifecycle and readiness logic flow,
and how domain rules, interfaces, and runtime-oriented helpers connect without
collapsing into one undifferentiated module.

These pages should let reviewers trace contract logic through real modules
instead of guessing from package names. The goal is to make the structure
legible enough that lifecycle, validation, and runtime-adjacent code can be
changed without quietly blurring ownership boundaries.

## Visual Summary

```mermaid
flowchart LR
    models["program and target models"]
    lifecycle["lifecycle and readiness logic"]
    domain["domain and biology rules"]
    interfaces["CLI and public entrypoints"]
    runtime["runtime adapters and execution helpers"]
    seams["integration seams<br/>foundation below, policy above"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    models --> lifecycle
    lifecycle --> domain
    domain --> interfaces
    domain --> runtime
    interfaces --> seams
    runtime --> seams
    class domain page;
    class models,lifecycle,interfaces,runtime positive;
    class seams caution;
```

## Start Here

- open [Module Map](module-map.md) for the fastest route to directory-level
  ownership
- open [Execution Model](execution-model.md) when the real question is how core
  rules move through the package
- open [Integration Seams](integration-seams.md) when a change may blur the
  boundary between core contracts and downstream policy
- open [Architecture Risks](architecture-risks.md) when structural clarity is
  under pressure from runtime or biology complexity

## Pages In This Section

- [Module Map](module-map.md)
- [Dependency Direction](dependency-direction.md)
- [Execution Model](execution-model.md)
- [State and Persistence](state-and-persistence.md)
- [Integration Seams](integration-seams.md)
- [Error Model](error-model.md)
- [Extensibility Model](extensibility-model.md)
- [Code Navigation](code-navigation.md)
- [Architecture Risks](architecture-risks.md)

## Use This Section When

- you need to trace structural ownership before refactoring contract logic
- you are checking whether lifecycle, domain, and runtime-adjacent code still
  respect a clear layering story
- you need to understand where contract logic ends and orchestration pressure
  begins

## Do Not Use This Section When

- the question is mainly about public commands, imports, schemas, or artifacts
- the issue is operational, such as validation workflow or release handling
- you need proof, risk posture, or done-ness criteria more than a structural map

## Read Across The Package

- open [Foundation](../foundation/index.md) when the structural issue is really
  an ownership question
- open [Interfaces](../interfaces/index.md) when architecture reaches a public
  contract or caller-facing surface
- open [Operations](../operations/index.md) when structure affects repeatable
  validation or release workflows
- open [Quality](../quality/index.md) when you need proof that the documented
  structure is still protected

## Concrete Anchors

- `src/bijux_proteomics/programs.py`, `targets.py`, and `program_spec.py` for
  durable program contracts
- `src/bijux_proteomics/lifecycle.py`, `validation.py`, and
  `execution_contracts.py` for lifecycle and readiness logic
- `src/bijux_proteomics/domain`, `biology`, `runtime_adapter.py`, and
  `interfaces/cli.py` for adjacent structural seams

## Reader Takeaway

Use `Architecture` to make the contract layer legible enough that a reviewer
can say where core rules live, how they flow, and where they meet neighboring
surfaces. If that answer depends on private memory rather than the docs and
code, the structure is too implicit.

## Purpose

This page introduces the architecture handbook for `bijux-proteomics-core` and
routes readers to the module, execution, seam, and risk pages that explain how
the package is organized.
