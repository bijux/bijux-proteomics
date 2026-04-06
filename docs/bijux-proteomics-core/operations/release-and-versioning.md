---
title: Release and Versioning
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-04
---

# Release and Versioning

Release work for `bijux-proteomics-core` depends on package metadata, tracked release notes, and
the repository's commit conventions.

The release path is part of the product story because it determines how readers
learn what changed and what stayed stable. This page should make package-local
release mechanics understandable without separating them from repository rules.

Treat the operations pages for `bijux-proteomics-core` as the package's explicit operating memory. They should make common tasks repeatable without relearning the workflow from logs or oral history.

## Visual Summary

```mermaid
flowchart RL
    page["Release and Versioning<br/>clarifies: repeat workflows | find diagnostics | release safely"]
    classDef page fill:#dbeafe,stroke:#1d4ed8,color:#1e3a8a,stroke-width:2px;
    classDef positive fill:#dcfce7,stroke:#16a34a,color:#14532d;
    classDef caution fill:#fee2e2,stroke:#dc2626,color:#7f1d1d;
    classDef anchor fill:#ede9fe,stroke:#7c3aed,color:#4c1d95;
    classDef action fill:#fef3c7,stroke:#d97706,color:#7c2d12;
    step1["HTTP app in src/bijux_proteomics/programs.py"]
    step1 --> page
    step2["packages/bijux-proteomics-core/pyproject.toml"]
    step2 --> page
    step3["CLI entrypoint in src/bijux_proteomics/interfaces/cli.py"]
    step3 --> page
    run1["tests/regression and tests/smoke for replay and storage protection"]
    page --> run1
    run2["tests/unit for api, contracts, core, interfaces, model, and runtime"]
    page --> run2
    run3["tests/e2e for governed flow behavior"]
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

- version file: `packages/bijux-proteomics-core/src/bijux_proteomics/_version.py`
- tag pattern is configured in `packages/bijux-proteomics-core/pyproject.toml`

## Concrete Anchors

- `packages/bijux-proteomics-core/pyproject.toml` for package metadata
- `packages/bijux-proteomics-core/README.md` for local package framing
- `packages/bijux-proteomics-core/tests` for executable operational backstops

## Use This Page When

- you are installing, running, diagnosing, or releasing the package
- you need repeatable operational anchors rather than architectural framing
- you are responding to package behavior in local work, CI, or incident pressure

## Decision Rule

Use `Release and Versioning` to decide whether a maintainer can repeat the package workflow from checked-in assets instead of memory. If a step works only because someone already knows the trick, the workflow is not documented clearly enough yet.

## What This Page Answers

- how `bijux-proteomics-core` is installed, run, diagnosed, and released in practice
- which checked-in files and tests anchor the operational story
- where a maintainer should look first when the package behaves differently

## Reviewer Lens

- verify that setup, workflow, and release statements still match package metadata and current commands
- check that operational guidance still points at real diagnostics and validation paths
- confirm that maintainer advice still works under current local and CI expectations

## Honesty Boundary

This page explains how `bijux-proteomics-core` is expected to be operated, but it does not replace package metadata, actual runtime behavior, or validation in a real environment. A workflow is only trustworthy if a maintainer can still repeat it from the checked-in assets named here.

## Next Checks

- move to interfaces when the operational path depends on a specific surface contract
- move to quality when the question becomes whether the workflow is sufficiently proven
- move back to architecture when operational complexity suggests a structural problem

## Purpose

This page ties package-local release mechanics to the wider repository release model.

## Stability

Keep it aligned with the package metadata and current versioning configuration.
