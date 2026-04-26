---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Dependency Governance

Dependency changes in `bijux-proteomics-intelligence` should be treated as contract changes when they
alter package authority, operational risk, or public setup expectations.

This page keeps dependency review from feeling bureaucratic. Dependencies
matter because they reshape what the package relies on, what it exposes, and
what downstream maintainers must now trust.

These quality pages show how `bijux-proteomics-intelligence` earns trust and where skepticism still belongs.

## Visual Summary

```mermaid
flowchart LR
    review1["recommendations stay inspectable"]
    review2["policy changes stay reviewable"]
    review3["outputs remain reproducible enough to judge"]
    page["bijux-proteomics-intelligence<br/>dependency governance"]
    proof1["ranking tests"]
    proof2["explanation checks"]
    proof3["policy review cases"]
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

## Current Dependency Themes

- agentic-proteins
- bijux-proteomics-foundation
- bijux-proteomics-intelligence
- bijux-proteomics-core
- duckdb
- pydantic

## Concrete Anchors

- tests/unit for api, contracts, core, interfaces, model, and runtime
- tests/e2e for governed flow behavior
- README.md

## Use This Page When

- you are reviewing tests, invariants, limitations, or ongoing risks
- you need evidence that the documented contract is actually defended
- you are deciding whether a change is truly done rather than merely implemented

## Decision Rule

Use `Dependency Governance` to decide whether `bijux-proteomics-intelligence` has actually earned trust after a change. If one narrow green check hides a wider contract, risk, or validation gap, the work is not done yet.

## What This Page Answers

- what currently proves the `bijux-proteomics-intelligence` contract instead of merely describing it
- which risks, limits, and assumptions still need explicit skepticism
- what a reviewer should be able to say before accepting a change as done

## Reviewer Lens

- compare the documented proof story with the actual test layout and release posture
- look for limitations or risks that should have moved with recent behavior changes
- verify that the claimed done-ness standard still reflects real validation practice

## Honesty Boundary

This page shows how `bijux-proteomics-intelligence` earns trust today, but prose is not the source of truth. If the listed tests, checks, and review practice stop backing the story, the story has to change.

## Next Checks

- move to foundation when the risk appears to be boundary confusion rather than missing tests
- move to architecture when the proof gap points to structural drift
- move to interfaces or operations when the proof question is really about a contract or workflow

## Purpose

This page shows why dependency review matters for the package.

## Stability

Keep it aligned with `pyproject.toml` and the package's real dependency posture.
