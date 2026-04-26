---
title: Installation and Setup
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Installation and Setup

Installation for `agentic-proteins` should start from the package metadata and the specific
optional dependencies that matter for the work being done.

This page exists to keep setup honest. A maintainer should be able to tell which
files actually define installation truth and which dependencies are merely
present in the environment for unrelated reasons.

These operations pages show how `agentic-proteins` is run and reviewed without forcing readers to reconstruct the workflow from logs or oral history.

## Visual Summary

```mermaid
flowchart LR
    step1["validate legacy imports"]
    step2["check legacy CLI paths"]
    step3["review alias retirement"]
    page["agentic-proteins<br/>installation and setup"]
    op1["migration operators"]
    op2["maintainers"]
    op3["release reviewers"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    step1 --> page
    step2 --> page
    step3 --> page
    page --> op1
    page --> op2
    page --> op3
    class page page;
    class step1,step2,step3 positive;
    class op1,op2,op3 anchor;
```

## Package Metadata Anchors

- package root: `packages/agentic-proteins`
- metadata file: `packages/agentic-proteins/pyproject.toml`
- readme: `packages/agentic-proteins/README.md`

## Dependency Themes

- agentic-proteins
- bijux-proteomics-foundation
- bijux-proteomics-intelligence
- bijux-proteomics-core
- duckdb
- pydantic

## Concrete Anchors

- `packages/agentic-proteins/pyproject.toml` for package metadata
- `packages/agentic-proteins/README.md` for local package framing
- `packages/agentic-proteins/tests` for executable operational backstops

## Use This Page When

- you are installing, running, diagnosing, or releasing the package
- you need repeatable operational anchors rather than architectural framing
- you are responding to package behavior in local work, CI, or incident pressure

## Decision Rule

Use `Installation and Setup` to decide whether a maintainer can repeat the package workflow from checked-in assets instead of memory. If a step works only because someone already knows the trick, the workflow is not documented clearly enough yet.

## What This Page Answers

- how `agentic-proteins` is installed, run, diagnosed, and released in practice
- which checked-in files and tests anchor the operational story
- where a maintainer should look first when the package behaves differently

## Reviewer Lens

- verify that setup, workflow, and release statements still match package metadata and current commands
- check that operational guidance still points at real diagnostics and validation paths
- confirm that maintainer advice still works under current local and CI expectations

## Honesty Boundary

This page shows how `agentic-proteins` is operated today, but the checked-in commands, artifacts, and validation remain the source of truth. Use those assets to confirm the workflow in a real environment.

## Next Checks

- move to interfaces when the operational path depends on a specific surface contract
- move to quality when the question becomes whether the workflow is sufficiently proven
- move back to architecture when operational complexity suggests a structural problem

## Purpose

This page tells maintainers where setup truth actually lives for the package.

## Stability

Keep it aligned with `pyproject.toml` and the checked-in package metadata.
