---
title: Failure Recovery
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Failure Recovery

Failure recovery starts with knowing which artifacts, interfaces, and tests expose the problem.

This page helps readers stabilize the situation before they try to
improve it. The first question is not always how to fix the bug; it is how to
locate the right evidence quickly.

These operations pages show how `bijux-proteomics-lab` is run and reviewed without forcing readers to reconstruct the workflow from logs or oral history.

## Visual Summary

```mermaid
flowchart LR
    signal1["workflow examples"]
    signal2["tests"]
    signal3["package metadata"]
    page["bijux-proteomics-lab<br/>failure recovery"]
    action1["trace the symptom"]
    action2["check the contract"]
    action3["leave review evidence"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    signal1 --> page
    signal2 --> page
    signal3 --> page
    page --> action1
    page --> action2
    page --> action3
    class page page;
    class signal1,signal2,signal3 anchor;
    class action1,action2,action3 action;
```

## Recovery Anchors

- interface surfaces: CLI entrypoint in src/bijux_proteomics_lab/planning.py, HTTP app in src/bijux_proteomics_lab/outcomes.py, lab contracts in src/bijux_proteomics_lab/schema.py
- artifacts to inspect: execution store records, replay decision artifacts, non-determinism policy evaluations
- tests to run: tests/unit for api, contracts, core, interfaces, model, and runtime, tests/e2e for governed flow behavior

## Concrete Anchors

- `packages/bijux-proteomics-lab/pyproject.toml` for package metadata
- `packages/bijux-proteomics-lab/README.md` for local package framing
- `packages/bijux-proteomics-lab/tests` for executable operational backstops

## Open This Page When

- you are installing, running, diagnosing, or releasing the package
- you need repeatable operational anchors rather than architectural framing
- you are responding to package behavior in local work, CI, or incident pressure

## Decision Rule

Use `Failure Recovery` to decide whether a maintainer can repeat the package workflow from checked-in assets instead of memory. If a step works only because someone already knows the trick, the workflow is not documented clearly enough yet.

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

- open interfaces when the operational path depends on a specific surface contract
- open quality when the question becomes whether the workflow is sufficiently proven
- move back to architecture when operational complexity suggests a structural problem

