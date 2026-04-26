---
title: Interfaces
audience: mixed
type: index
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Interfaces

This section shows which core surfaces are real contracts: commands, imports,
schemas, artifacts, and examples that other packages or operators can rely on
when they build against durable program rules.

These pages stop callers from depending on incidental implementation details
when what they really need is the explicit contract layer. For core,
that matters because lifecycle and readiness assumptions spread quickly into
knowledge, intelligence, lab, and runtime behavior.

## Visual Summary

```mermaid
flowchart LR
    cli["CLI and operator entrypoints"]
    imports["public imports"]
    schemas["program and lifecycle schemas"]
    artifacts["contract artifacts<br/>and examples"]
    workflows["operator workflows<br/>how contracts are exercised"]
    review["compatibility review<br/>what changes need extra care"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    cli --> schemas
    imports --> schemas
    schemas --> artifacts
    artifacts --> workflows
    schemas --> review
    class schemas page;
    class cli,imports,artifacts positive;
    class workflows anchor;
    class review action;
```

## Start Here

- open [CLI Surface](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/cli-surface/) when the dependency begins with operator or
  validation commands
- open [Data Contracts](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/data-contracts/) when the real question is lifecycle,
  readiness, or program schema meaning
- open [Public Imports](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/public-imports/) when the caller depends on Python
  entrypoints rather than CLI usage
- open [Compatibility Commitments](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/compatibility-commitments/) when a contract
  change may ripple into higher packages

## Published Interface Pages

- [CLI Surface](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/cli-surface/)
- [API Surface](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/api-surface/)
- [Configuration Surface](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/configuration-surface/)
- [Data Contracts](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/data-contracts/)
- [Artifact Contracts](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/artifact-contracts/)
- [Entrypoints and Examples](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/entrypoints-and-examples/)
- [Operator Workflows](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/operator-workflows/)
- [Public Imports](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/public-imports/)
- [Compatibility Commitments](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/interfaces/compatibility-commitments/)

## Use This Section When

- you need to know which core surface is deliberate and supportable
- higher packages depend on lifecycle, readiness, or program contracts
- you are reviewing whether a change creates compatibility pressure across the
  proteomics stack

## Do Not Use This Section When

- the real question is why the rule belongs in core at all
- you need structural layout or contract-code organization first
- the issue is operational, such as validation workflow, release steps, or test
  execution

## Read Across The Package

- open [Foundation](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/foundation/) when the contract concern is really
  a boundary or ownership question
- open [Architecture](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/architecture/) when the surface depends on
  deeper lifecycle, domain, or runtime-adjacent structure
- open [Operations](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/operations/) when you need repeatable workflows
  for exercising or shipping core contracts
- open [Quality](https://bijux.io/bijux-proteomics/04-bijux-proteomics-core/quality/) when the real issue is whether the
  documented contract is sufficiently defended

## Concrete Anchors

- CLI entrypoint in `src/bijux_proteomics/interfaces/cli.py`
- core contracts in `src/bijux_proteomics/programs.py`,
  `lifecycle.py`, and `validation.py`
- public exports in `src/bijux_proteomics/__init__.py`
- execution contract helpers in `src/bijux_proteomics/execution_contracts.py`

## Reader Takeaway

Use `Interfaces` to separate stable core contracts from whatever merely happens
to be visible in the implementation. If another package cannot defend its
dependency in terms of named commands, imports, schemas, artifacts, examples,
and tests, that dependency is not yet an honest public surface.

## Purpose

This page shows the published interface routes for `bijux-proteomics-core` and
the supported surfaces that higher packages and operators can rely on.
