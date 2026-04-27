---
title: Package Overview
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-knowledge-docs
last_reviewed: 2026-04-26
---

# Package Overview

`bijux-proteomics-knowledge` exists to keep claims, evidence, confidence, and contradiction state explicit and reviewable. The package is useful only when that
role stays narrow enough that a reviewer can say why it exists without naming
several different owners at once.

## What It Owns

- track claims and evidence records
- model confidence and contradiction state
- provide repositories and review seams for knowledge state

## What It Refuses

- scoring policy
- lab workflow ownership
- operator-facing runtime behavior

## First Proof Check

- `packages/bijux-proteomics-knowledge/src/bijux_proteomics_knowledge`
- `packages/bijux-proteomics-knowledge/tests`
- neighboring handbook branches once a change crosses the local role
