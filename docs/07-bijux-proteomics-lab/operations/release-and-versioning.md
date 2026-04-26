---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Release and Versioning

Release work for `bijux-proteomics-lab` depends on package metadata, tracked release notes, and
the repository's commit conventions.

The release path is part of the product story because it determines how readers
learn what changed and what stayed stable. This page makes package-local
release mechanics understandable without separating them from repository rules.

These operations pages show how `bijux-proteomics-lab` is run and reviewed without forcing readers to reconstruct the workflow from logs or oral history.

## Visual Summary

```mermaid
flowchart LR
    guard1["keep planning reproducible"]
    guard2["show outcome handoff"]
    guard3["treat execution gaps as first-class"]
    page["bijux-proteomics-lab<br/>release and versioning"]
    proof1["workflow examples"]
    proof2["tests"]
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

## Release Anchors

- README.md
- CHANGELOG.md
- pyproject.toml

## Versioning Anchors

- release version is explicit in `packages/bijux-proteomics-lab/pyproject.toml`
- release tags follow `v*` and release workflows are triggered from those tags

## Concrete Anchors

- `packages/bijux-proteomics-lab/pyproject.toml` for package metadata
- `packages/bijux-proteomics-lab/README.md` for local package framing
- `packages/bijux-proteomics-lab/tests` for executable operational backstops

## Open This Page When

- you are installing, running, diagnosing, or releasing the package
- you need repeatable operational anchors rather than architectural framing
- you are responding to package behavior in local work, CI, or incident pressure

## Decision Rule

Use `Release and Versioning` to decide whether a maintainer can repeat the package workflow from checked-in assets instead of memory. If a step works only because someone already knows the trick, the workflow is not documented clearly enough yet.

## What This Page Answers

- how `bijux-proteomics-lab` is installed, run, diagnosed, and released in practice
- which checked-in files and tests anchor the operational story
- where a maintainer should look first when the package behaves differently

## Reviewer Lens

- verify that setup, workflow, and release statements still match package metadata and current commands
- check that operational guidance still points at real diagnostics and validation paths
- confirm that maintainer advice still works under current local and CI expectations

## Honesty Boundary

This page shows how `bijux-proteomics-lab` is operated today, but the checked-in commands, artifacts, and validation remain the source of truth. Use those assets to confirm the workflow in a real environment.

## Next Checks

- move to interfaces when the operational path depends on a specific surface contract
- move to quality when the question becomes whether the workflow is sufficiently proven
- move back to architecture when operational complexity suggests a structural problem

## Purpose

This page ties package-local release mechanics to the wider repository release model.

## Stability

Keep it aligned with the package metadata and current versioning configuration.
