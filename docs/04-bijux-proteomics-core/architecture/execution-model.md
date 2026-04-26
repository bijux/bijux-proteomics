---
title: Execution Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Execution Model

`bijux-proteomics-core` executes work by receiving inputs at its interfaces, coordinating policy
and workflows in application code, and delegating specific responsibilities to
owned modules.

This page gives a reader one clean story about how work moves through the
package. The goal is not to describe every branch, but to make the main path
recognizable before someone opens the implementation.

Read the architecture pages as a reviewer-facing map of structure and flow for
`bijux-proteomics-core`. They shorten code reading without trying to replace it.

## Visual Summary

```mermaid
flowchart LR
    in1["foundation payloads"]
    in2["program change proposals"]
    in3["validation requirements"]
    page["bijux-proteomics-core<br/>execution model"]
    out1["knowledge state transitions"]
    out2["intelligence policy inputs"]
    out3["runtime execution constraints"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    in1 --> page
    in2 --> page
    in3 --> page
    page --> out1
    page --> out2
    page --> out3
    class page page;
    class in1,in2,in3 anchor;
    class out1,out2,out3 positive;
```

## Execution Anchors

- entry surfaces: CLI entrypoint in src/bijux_proteomics/interfaces/cli.py, HTTP app in src/bijux_proteomics/programs.py, program schemas in src/bijux_proteomics/programs.py
- workflow modules: src/bijux_proteomics/model, src/bijux_proteomics/runtime, src/bijux_proteomics/application
- outputs: execution store records, replay decision artifacts, non-determinism policy evaluations

## Concrete Anchors

- `src/bijux_proteomics/model` for durable runtime models
- `src/bijux_proteomics/runtime` for execution engines and lifecycle logic
- `src/bijux_proteomics/application` for orchestration and replay coordination

## Use This Page When

- you are tracing structure, execution flow, or dependency pressure
- you need to understand how modules fit before refactoring
- you are reviewing design drift rather than one isolated bug

## Decision Rule

Use `Execution Model` to decide whether a structural change makes `bijux-proteomics-core` easier or harder to explain in terms of modules, dependency direction, and execution flow. If the change works only because the design becomes harder to read, the safer answer is redesign rather than acceptance.

## What This Page Answers

- how `bijux-proteomics-core` is organized internally in terms a reviewer can follow
- which modules carry the main execution and dependency story
- where structural drift would show up before it becomes expensive

## Reviewer Lens

- trace the described execution path through the named modules instead of trusting the diagram alone
- look for dependency direction or layering that now contradicts the documented seam
- verify that the structural risks named here still match the current code shape

## Honesty Boundary

This page describes the current structural model of `bijux-proteomics-core`, but it does not guarantee that every import path or runtime path still obeys that model. Readers should treat it as a map that must stay aligned with code and tests, not as an authority above them.

## Next Checks

- open interfaces when the review reaches a public or operator-facing seam
- open operations when the concern becomes repeatable runtime behavior
- open quality when you need proof that the documented structure is still protected

## Purpose

This page summarizes the package execution model before readers inspect individual modules.

## Stability

Keep it aligned with the actual workflow code and entrypoints.
