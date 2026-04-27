---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-intelligence-docs
last_reviewed: 2026-04-26
---

# Package Overview

`bijux-proteomics-intelligence` exists to turn evidence and program constraints into scores, scenarios, recommendations, and explanations. The package is useful only when that
role stays narrow enough that a reviewer can say why it exists without naming
several different owners at once.

## What It Owns

- score and rank candidates
- evaluate scenarios and loops
- render explanations and reports for decisions

## What It Refuses

- evidence truth and contradiction state
- durable program contracts
- execution orchestration

## First Proof Check

- `packages/bijux-proteomics-intelligence/src/bijux_proteomics_intelligence`
- `packages/bijux-proteomics-intelligence/tests`
- neighboring handbook branches once a change crosses the local role
