---
title: Code Navigation
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Code Navigation

When you need to understand a change in `bijux-proteomics-lab`, use this reading order:

This page is intentionally practical. Its purpose is to shorten the path from a
question in review to the files that actually explain the answer.

Treat the architecture pages for `bijux-proteomics-lab` as a reviewer-facing map of structure and flow. They shorten code reading instead of trying to replace it.

## Visual Summary

```mermaid
flowchart LR
    q1["where is the main behavior?"]
    q2["where do contracts surface?"]
    q3["where does drift show up?"]
    page["bijux-proteomics-lab<br/>code navigation"]
    code1["src/bijux_proteomics_lab"]
    code2["tests"]
    code3["adjacent handbook pages"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    q1 --> page
    q2 --> page
    q3 --> page
    page --> code1
    page --> code2
    page --> code3
    class page page;
    class q1,q2,q3 action;
    class code1,code2,code3 anchor;
```

## Reading Order

- start at the relevant interface or API module
- move into the owning application or domain module
- finish in the tests that protect the behavior

## Concrete Anchors

- `src/bijux_proteomics_lab/model` for durable runtime models
- `src/bijux_proteomics_lab/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics_lab/application` for orchestration and replay coordination
- `src/bijux_proteomics_lab/verification` for runtime-level validation support
- `src/bijux_proteomics_lab/interfaces` for CLI surfaces and manifest loading
- `src/bijux_proteomics_lab/api` for HTTP application surfaces

## Test Anchors

- tests/unit for api, contracts, core, interfaces, model, and runtime
- tests/e2e for governed flow behavior
- tests/regression and tests/smoke for replay and storage protection
- tests/golden for durable example fixtures

## Concrete Anchors

- `src/bijux_proteomics_lab/model` for durable runtime models
- `src/bijux_proteomics_lab/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics_lab/application` for orchestration and replay coordination

## Open This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Code Navigation` to decide whether a structural change makes `bijux-proteomics-lab` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

## What You Can Resolve Here

- how `bijux-proteomics-lab` is organized internally in terms a reviewer can follow
- which modules carry the main execution and dependency story
- where structural drift would show up before it becomes expensive

## Review Focus

- trace the described execution path through the named modules instead of trusting the diagram alone
- look for dependency direction or layering that now contradicts the documented seam
- verify that the structural risks named here still match the current code shape

## Limits

This page describes the current structural model of `bijux-proteomics-lab`, but it does not guarantee that every import path or runtime path still obeys that model. Treat it as a map that must stay aligned with code and tests, not as an authority above them.

## Read Next

- open interfaces when the review reaches a public or operator-facing seam
- open operations when the concern becomes repeatable runtime behavior
- open quality when you need proof that the documented structure is still protected

