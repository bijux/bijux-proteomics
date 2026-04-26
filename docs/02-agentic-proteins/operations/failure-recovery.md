---
title: Failure Recovery
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-04
---

# Failure Recovery

Failure recovery starts with knowing which artifacts, interfaces, and tests expose the problem.

This page should help a maintainer stabilize the situation before they try to
improve it. The first question is not always how to fix the bug; it is how to
locate the right evidence quickly.

Treat the operations pages for `agentic-proteins` as the package's explicit operating memory. They should make common tasks repeatable without relearning the workflow from logs or oral history.

## Visual Summary

```mermaid
flowchart TB
    page["Failure Recovery<br/>clarifies: repeat workflows | find diagnostics | release safely"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    step1["packages/agentic-proteins/pyproject.toml"]
    step1 --> page
    step2["CLI entrypoint in src/agentic_proteins/interfaces/cli.py"]
    step2 --> page
    step3["HTTP app in src/agentic_proteins/api/v1"]
    step3 --> page
    run1["tests/unit for api, contracts, core, interfaces, model, and runtime"]
    page --> run1
    run2["tests/e2e for governed flow behavior"]
    page --> run2
    run3["tests/regression and tests/smoke for replay and storage protection"]
    page --> run3
    release1["README.md"]
    run1 --> release1
    release2["CHANGELOG.md"]
    run2 --> release2
    release3["pyproject.toml"]
    run3 --> release3
    class page page;
    class step1,step2,step3 positive;
    class run1,run2,run3 anchor;
    class release1,release2,release3 action;
```

## Recovery Anchors

- interface surfaces: CLI entrypoint in src/agentic_proteins/interfaces/cli.py, HTTP app in src/agentic_proteins/api/v1, shared API schema in apis/agentic-proteins/v1
- artifacts to inspect: execution store records, replay decision artifacts, non-determinism policy evaluations
- tests to run: tests/unit for api, contracts, core, interfaces, model, and runtime, tests/e2e for governed flow behavior

## Concrete Anchors

- `packages/agentic-proteins/pyproject.toml` for package metadata
- `packages/agentic-proteins/README.md` for local package framing
- `packages/agentic-proteins/tests` for executable operational backstops

## Use This Page When

- you are installing, running, diagnosing, or releasing the package
- you need repeatable operational anchors rather than architectural framing
- you are responding to package behavior in local work, CI, or incident pressure

## Decision Rule

Use `Failure Recovery` to decide whether a maintainer can repeat the package workflow from checked-in assets instead of memory. If a step works only because someone already knows the trick, the workflow is not documented clearly enough yet.

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

This page gives maintainers a durable frame for triaging package failures.

## Stability

Keep it aligned with the package entrypoints and diagnostic outputs.
