---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Dependency Governance

Dependency changes in `bijux-proteomics-lab` should be treated as contract changes when they
alter package authority, operational risk, or public setup expectations.

This page should keep dependency review from feeling bureaucratic. Dependencies
matter because they reshape what the package relies on, what it exposes, and
what downstream maintainers must now trust.

Treat the quality pages for `bijux-proteomics-lab` as the proof frame around the package. They should show how trust is earned and where skepticism still belongs.

## Visual Summary

```mermaid
flowchart LR
    review1["plans stay reproducible"]
    review2["outcomes stay connected to evidence"]
    review3["promotion remains reviewable"]
    page["bijux-proteomics-lab<br/>dependency governance"]
    proof1["planning tests"]
    proof2["outcome linkage checks"]
    proof3["rerun and promotion checks"]
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

Use `Dependency Governance` to decide whether `bijux-proteomics-lab` has actually earned trust after a change. If one narrow green check hides a wider contract, risk, or validation gap, the work is not done yet.

## What This Page Answers

- what currently proves the `bijux-proteomics-lab` contract instead of merely describing it
- which risks, limits, and assumptions still need explicit skepticism
- what a reviewer should be able to say before accepting a change as done

## Reviewer Lens

- compare the documented proof story with the actual test layout and release posture
- look for limitations or risks that should have moved with recent behavior changes
- verify that the claimed done-ness standard still reflects real validation practice

## Honesty Boundary

This page explains how `bijux-proteomics-lab` is supposed to earn trust, but it does not claim that prose alone is enough. If the listed tests, checks, and review practice stop backing the story, the story has to change.

## Next Checks

- move to foundation when the risk appears to be boundary confusion rather than missing tests
- move to architecture when the proof gap points to structural drift
- move to interfaces or operations when the proof question is really about a contract or workflow

## Purpose

This page explains why dependency review matters for the package.

## Stability

Keep it aligned with `pyproject.toml` and the package's real dependency posture.
