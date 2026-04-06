---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-04
---

# Release and Versioning

Release work for `agentic-proteins` depends on package metadata, tracked release notes, and
the repository's commit conventions.

The release path is part of the product story because it determines how readers
learn what changed and what stayed stable. This page should make package-local
release mechanics understandable without separating them from repository rules.

Treat the operations pages for `agentic-proteins` as the package's explicit operating memory. They should make common tasks repeatable without relearning the workflow from logs or oral history.

## Visual Summary

```mermaid
flowchart RL
    page["Release and Versioning<br/>clarifies: repeat workflows | find diagnostics | release safely"]
    classDef page fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a,stroke-width:2px;
    classDef positive fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef caution fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
    classDef anchor fill:#ede9fe,stroke:#7c3aed,color:#4c1d95;
    classDef action fill:#fef3c7,stroke:#d97706,color:#7c2d12;
    step1["HTTP surface in src/agentic_proteins/api/"]
    step1 --> page
    step2["packages/agentic-proteins/pyproject.toml"]
    step2 --> page
    step3["CLI entrypoint in src/agentic_proteins/interfaces/cli.py"]
    step3 --> page
    run1["tests/regression for runtime guardrails and replay stability"]
    page --> run1
    run2["tests/unit and tests/integration for package contracts"]
    page --> run2
    run3["tests/e2e for governed workflow behavior"]
    page --> run3
    release1["pyproject.toml"]
    run1 --> release1
    release2["README.md"]
    run2 --> release2
    release3["CHANGELOG.md"]
    run3 --> release3
    class page page;
    class step1,step2,step3 positive;
    class run1,run2,run3 anchor;
    class release1,release2,release3 action;
```

## Release Anchors

- README.md
- CHANGELOG.md
- pyproject.toml

## Versioning Anchors

- version is resolved from Git tags through `hatch-vcs` in `packages/agentic-proteins/pyproject.toml`
- release tags follow `v*` and publish workflows are triggered from those tags

## Concrete Anchors

- `packages/agentic-proteins/pyproject.toml` for package metadata
- `packages/agentic-proteins/README.md` for local package framing
- `packages/agentic-proteins/tests` for executable operational backstops

## Use This Page When

- you are installing, running, diagnosing, or releasing the package
- you need repeatable operational anchors rather than architectural framing
- you are responding to package behavior in local work, CI, or incident pressure

## Decision Rule

Use `Release and Versioning` to decide whether a maintainer can repeat the package workflow from checked-in assets instead of memory. If a step works only because someone already knows the trick, the workflow is not documented clearly enough yet.

## What This Page Answers

- how `agentic-proteins` is installed, run, diagnosed, and released in practice
- which checked-in files and tests anchor the operational story
- where a maintainer should look first when the package behaves differently

## Reviewer Lens

- verify that setup, workflow, and release statements still match package metadata and current commands
- check that operational guidance still points at real diagnostics and validation paths
- confirm that maintainer advice still works under current local and CI expectations

## Honesty Boundary

This page explains how `agentic-proteins` is expected to be operated, but it does not replace package metadata, actual runtime behavior, or validation in a real environment. A workflow is only trustworthy if a maintainer can still repeat it from the checked-in assets named here.

## Next Checks

- move to interfaces when the operational path depends on a specific surface contract
- move to quality when the question becomes whether the workflow is sufficiently proven
- move back to architecture when operational complexity suggests a structural problem

## Purpose

This page ties package-local release mechanics to the wider repository release model.

## Stability

Keep it aligned with the package metadata and current versioning configuration.
