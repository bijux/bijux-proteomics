---
title: Operations
audience: mixed
type: index
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Operations

This section explains how to validate, run, diagnose, and release
`agentic-proteins` as a compatibility bridge rather than as a primary runtime
package.

These pages are the checked-in operating memory for the legacy bridge. They
should help a maintainer verify forwarding behavior, diagnose broken aliases,
and judge retirement readiness without relying on CI archaeology or private
migration habits.

This section makes one posture obvious: operational work here exists to
keep migration safe and temporary, not to expand the long-term operating center
of the repository.

## Visual Summary

```mermaid
flowchart LR
    f1["validate legacy imports"]
    f2["check legacy CLI paths"]
    f3["review alias retirement"]
    page["Operations section<br/>repeatable package workflows"]
    next1["setup and workflows"]
    next2["diagnostics and recovery"]
    next3["release and deployment"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    f1 --> page
    f2 --> page
    f3 --> page
    page --> next1
    page --> next2
    page --> next3
    class page page;
    class f1,f2,f3 positive;
    class next1,next2,next3 anchor;
```

## Pages in This Section

- [Installation and Setup](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/installation-and-setup/)
- [Local Development](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/local-development/)
- [Common Workflows](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/common-workflows/)
- [Observability and Diagnostics](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/observability-and-diagnostics/)
- [Performance and Scaling](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/performance-and-scaling/)
- [Failure Recovery](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/failure-recovery/)
- [Release and Versioning](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/release-and-versioning/)
- [Security and Safety](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/security-and-safety/)
- [Deployment Boundaries](https://bijux.io/bijux-proteomics/02-agentic-proteins/operations/deployment-boundaries/)

## Open This Section When

- you are validating legacy imports, CLI aliases, or compatibility release
  behavior
- you need to diagnose forwarding failures or retirement blockers
- the question is operational and still specific to the compatibility bridge

## Open Another Section When

- the real workflow concern belongs to canonical runtime operations
- you are treating the compatibility package as the preferred place for normal
  runtime execution
- the issue is about caller contracts or package structure rather than
  repeatable operations

## Bottom Line

This section keeps keep the bridge safe while it still ships. If an
operational question remains important after the legacy alias disappears, the
canonical runtime handbook is the better long-term home.

## Read Across the Package

- [Foundation](https://bijux.io/bijux-proteomics/02-agentic-proteins/foundation/) when you need the package boundary and ownership story first
- [Architecture](https://bijux.io/bijux-proteomics/02-agentic-proteins/architecture/) when the question becomes structural, modular, or execution-oriented
- [Interfaces](https://bijux.io/bijux-proteomics/02-agentic-proteins/interfaces/) when the question becomes caller-facing, schema-facing, or contract-facing
- [Quality](https://bijux.io/bijux-proteomics/02-agentic-proteins/quality/) when the question becomes proof, risk, trust, or review sufficiency

## Concrete Anchors

- `packages/agentic-proteins/pyproject.toml` for package metadata
- `packages/agentic-proteins/README.md` for local package framing
- `packages/agentic-proteins/tests` for executable operational backstops

## Open This Page When

- you are installing, running, diagnosing, or releasing the package
- you need repeatable operational anchors rather than architectural framing
- you are responding to package behavior in local work, CI, or incident pressure

## Decision Rule

Use `Operations` to decide whether a maintainer can repeat the package workflow from checked-in assets instead of memory. If a step works only because someone already knows the trick, the workflow is not documented clearly enough yet.

## What You Can Resolve Here

- how `agentic-proteins` is installed, run, diagnosed, and released in practice
- which checked-in files and tests anchor the operational story
- where a maintainer should look first when the package behaves differently

## Review Focus

- verify that setup, workflow, and release statements still match package metadata and current commands
- check that operational guidance still points at real diagnostics and validation paths
- confirm that maintainer advice still works under current local and CI expectations

## Limits

Checked-in commands, artifacts, and validation remain the source of truth for this workflow.

## Read Next

- open interfaces when the operational path depends on a specific surface contract
- open quality when the question becomes whether the workflow is sufficiently proven
- open architecture when operational complexity suggests a structural problem

