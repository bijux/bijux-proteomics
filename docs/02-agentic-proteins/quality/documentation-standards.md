---
title: Documentation Standards
audience: mixed
type: explanation
status: canonical
owner: agentic-proteins-docs
last_reviewed: 2026-04-26
---

# Documentation Standards

Package docs should stay consistent with the shared handbook layout used across the repository.

Consistency matters here because readers should not need to relearn how to read
every package. The shared layout is part of the user experience, but honesty is
more important than uniformity for its own sake.

These quality pages show how `agentic-proteins` earns trust and where skepticism still belongs.

## Visual Summary

```mermaid
flowchart LR
    review1["compatibility still works"]
    review2["new work stays elsewhere"]
    review3["retirement is evidence-based"]
    page["agentic-proteins<br/>documentation standards"]
    proof1["forwarding tests"]
    proof2["alias coverage"]
    proof3["retirement review checks"]
    classDef page fill:var(--bijux-mermaid-page-fill),stroke:var(--bijux-mermaid-page-stroke),color:var(--bijux-mermaid-page-text),stroke-width:2px;
    classDef positive fill:var(--bijux-mermaid-positive-fill),stroke:var(--bijux-mermaid-positive-stroke),color:var(--bijux-mermaid-positive-text);
    classDef caution fill:var(--bijux-mermaid-caution-fill),stroke:var(--bijux-mermaid-caution-stroke),color:var(--bijux-mermaid-caution-text);
    classDef anchor fill:var(--bijux-mermaid-anchor-fill),stroke:var(--bijux-mermaid-anchor-stroke),color:var(--bijux-mermaid-anchor-text);
    classDef action fill:var(--bijux-mermaid-action-fill),stroke:var(--bijux-mermaid-action-stroke),color:var(--bijux-mermaid-action-text);
    review1 --> page
    review2 --> page
    review3 --> page
    page --> proof1
    page --> proof2
    page --> proof3
    class page page;
    class review1,review2,review3 action;
    class proof1,proof2,proof3 anchor;
```

## Standards

- use the shared five-category package spine
- prefer stable filenames that describe durable intent
- keep docs grounded in real code paths, interfaces, and artifacts

## Concrete Anchors

- tests/unit for api, contracts, core, interfaces, model, and runtime
- tests/e2e for governed flow behavior
- README.md

## Open This Page When

- you are reviewing tests, invariants, limitations, or ongoing risks
- you need evidence that the documented contract is actually defended
- you are deciding whether a change is truly done rather than merely implemented

## Decision Rule

Use `Documentation Standards` to decide whether `agentic-proteins` has actually earned trust after a change. If one narrow green check hides a wider contract, risk, or validation gap, the work is not done yet.

## What This Page Answers

- what currently proves the `agentic-proteins` contract instead of merely describing it
- which risks, limits, and assumptions still need explicit skepticism
- what a reviewer should be able to say before accepting a change as done

## Reviewer Lens

- compare the documented proof story with the actual test layout and release posture
- look for limitations or risks that should have moved with recent behavior changes
- verify that the claimed done-ness standard still reflects real validation practice

## Honesty Boundary

This page shows how `agentic-proteins` earns trust today, but prose is not the source of truth. If the listed tests, checks, and review practice stop backing the story, the story has to change.

## Next Checks

- move to foundation when the risk appears to be boundary confusion rather than missing tests
- move to architecture when the proof gap points to structural drift
- move to interfaces or operations when the proof question is really about a contract or workflow

## Purpose

This page keeps package docs from drifting back into ad hoc structure.

## Stability

Update it only when the shared documentation system itself changes.
