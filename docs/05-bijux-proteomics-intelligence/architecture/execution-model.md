---
title: Execution Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Execution Model

The execution model for `bijux-proteomics-intelligence` should make it clear how package-owned work progresses without quietly taking over a neighbor's job.

## Flow

- candidate and metric inputs enter through candidate and domain models
- policies and evaluators score, compare, and rank those inputs
- reports, briefs, outcomes, and design-loop modules explain the decision and track whether progress is converging

## First Proof Check

- the owning modules for each flow stage
- package tests that prove the transition points
- downstream or upstream handbooks when the flow crosses package boundaries
