---
title: Security and Safety
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Security and Safety

Security review in `agentic-proteins` should focus on the package's real boundary surfaces and outputs.

This page keeps safety work concrete. A useful security discussion starts from
the actual interfaces, artifacts, and authority the package holds, not from
generic caution language detached from the codebase.

These operations pages show how `agentic-proteins` is run and reviewed without forcing readers to reconstruct the workflow from logs or oral history.

## Visual Summary

```mermaid
flowchart LR
    guard1["do not add new runtime features"]
    guard2["keep the bridge narrow"]
    guard3["retire unused aliases"]
    page["agentic-proteins<br/>security and safety"]
    proof1["compatibility tests"]
    proof2["runtime handoff docs"]
    proof3["package metadata"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    guard1 --> page
    guard2 --> page
    guard3 --> page
    page --> proof1
    page --> proof2
    page --> proof3
    class page page;
    class guard1,guard2,guard3 action;
    class proof1,proof2,proof3 anchor;
```

## Review Anchors

- CLI entrypoint in src/agentic_proteins/interfaces/cli.py
- HTTP app in src/agentic_proteins/api/v1
- shared API schema in apis/agentic-proteins/v1

## Safety Rule

Any change that broadens package authority should update docs, tests, and release notes together.

## Concrete Anchors

- `packages/agentic-proteins/pyproject.toml` for package metadata
- `packages/agentic-proteins/README.md` for local package framing
- `packages/agentic-proteins/tests` for executable operational backstops

## Use This Page When

- you are installing, running, diagnosing, or releasing the package
- you need repeatable operational anchors rather than architectural framing
- you are responding to package behavior in local work, CI, or incident pressure

## Decision Rule

Use `Security and Safety` to decide whether a maintainer can repeat the package workflow from checked-in assets instead of memory. If a step works only because someone already knows the trick, the workflow is not documented clearly enough yet.

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

This page keeps security review grounded in concrete package seams.

## Stability

Keep it aligned with the package interfaces and operational risk profile.
