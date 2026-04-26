---
title: Execution Model
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-core-docs
last_reviewed: 2026-04-26
---

# Execution Model

The execution model for `bijux-proteomics-core` should make it clear how package-owned work progresses without quietly taking over a neighbor's job.

## Flow

- program and target definitions state what a run means at the contract level
- lifecycle, validation, and execution-contract modules decide readiness and allowed transitions
- runtime-facing adapters expose those rules to execution layers without transferring ownership of them

## First Proof Check

- the owning modules for each flow stage
- package tests that prove the transition points
- downstream or upstream handbooks when the flow crosses package boundaries
