---
title: Dependency Governance
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-foundation-docs
last_reviewed: 2026-04-04
---

# Dependency Governance

Dependency changes in `bijux-proteomics-foundation` should be treated as contract changes when they
alter package authority, operational risk, or public setup expectations.

This page should keep dependency review from feeling bureaucratic. Dependencies
matter because they reshape what the package relies on, what it exposes, and
what downstream maintainers must now trust.

Treat the quality pages for `bijux-proteomics-foundation` as the proof frame around the package. They should show how trust is earned and where skepticism still belongs.

## Visual Summary

```mermaid
flowchart LR
    dep["new or changed dependency"] --> q1{"needed for package purpose?"}
    q1 -->|no| reject["reject"]
    q1 -->|yes| q2{"fits dependency direction?"}
    q2 -->|no| redesign["redesign placement"]
    q2 -->|yes| q3{"risk acceptable?"}
    q3 -->|no| mitigate["pin, isolate, or replace"]
    q3 -->|yes| accept["accept with review note"]
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

Use `Dependency Governance` to decide whether `bijux-proteomics-foundation` has actually earned trust after a change. If one narrow green check hides a wider contract, risk, or validation gap, the work is not done yet.

## What This Page Answers

- what currently proves the `bijux-proteomics-foundation` contract instead of merely describing it
- which risks, limits, and assumptions still need explicit skepticism
- what a reviewer should be able to say before accepting a change as done

## Reviewer Lens

- compare the documented proof story with the actual test layout and release posture
- look for limitations or risks that should have moved with recent behavior changes
- verify that the claimed done-ness standard still reflects real validation practice

## Honesty Boundary

This page explains how `bijux-proteomics-foundation` is supposed to earn trust, but it does not claim that prose alone is enough. If the listed tests, checks, and review practice stop backing the story, the story has to change.

## Next Checks

- move to foundation when the risk appears to be boundary confusion rather than missing tests
- move to architecture when the proof gap points to structural drift
- move to interfaces or operations when the proof question is really about a contract or workflow

## Purpose

This page explains why dependency review matters for the package.

## Stability

Keep it aligned with `pyproject.toml` and the package's real dependency posture.
