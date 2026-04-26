---
title: Review Checklist
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-lab-docs
last_reviewed: 2026-04-26
---

# Review Checklist

Reviewing changes in `bijux-proteomics-lab` should include both behavior and documentation.

The checklist is not here to slow people down with ceremony. It is here to stop
fast review from becoming shallow review when a change touches boundaries,
contracts, or proof.

Treat the quality pages for `bijux-proteomics-lab` as the proof frame around the package. They should show how trust is earned and where skepticism still belongs.

## Visual Summary

```mermaid
flowchart LR
    review1["plans stay reproducible"]
    review2["outcomes stay connected to evidence"]
    review3["promotion remains reviewable"]
    page["bijux-proteomics-lab<br/>review checklist"]
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

## Checklist

- did ownership stay inside the correct package boundary
- do interface or artifact changes have matching docs and tests
- are filenames, commit messages, and symbols still clear enough to age well

## Concrete Anchors

- tests/unit for api, contracts, core, interfaces, model, and runtime
- tests/e2e for governed flow behavior
- README.md

## Use This Page When

- you are reviewing tests, invariants, limitations, or ongoing risks
- you need evidence that the documented contract is actually defended
- you are deciding whether a change is truly done rather than merely implemented

## Decision Rule

Use `Review Checklist` to decide whether `bijux-proteomics-lab` has actually earned trust after a change. If one narrow green check hides a wider contract, risk, or validation gap, the work is not done yet.

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

This page records a compact review lens for package changes.

## Stability

Update it only when the package review posture genuinely changes.
