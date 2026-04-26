---
title: Agentic Module Ledger Summary
audience: maintainer
type: reference
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-04-26
---

# agentic-proteins Module Migration Ledger Summary

This summary gives the current migration posture in one page. The signal is where ownership is already clear and where review debt is still concentrated.

## Current Counts

- total modules: 148
- `runtime_execution_ownership`: 54
- `runtime_support_internal_review`: 64
- `domain_ownership`: 30

About 36 percent of the ledger is already classified as clear runtime execution ownership, about 43 percent still needs internal review, and about 20 percent is already marked for lower-layer ownership.

## Target Owner Distribution

- `bijux-proteomics-runtime`: 117
- `bijux-proteomics-intelligence`: 16
- `bijux-proteomics-core`: 12
- `bijux-proteomics-knowledge`: 2
- `agentic-proteins-compat`: 1

## Review Hotspots

- `agents/**`: 22 review-required modules
- `core/**`: 16 review-required modules
- `execution/**`: 7 review-required modules

## What The Numbers Mean

The main ambiguity is no longer the public runtime surface. The harder work is mixed support code where older modules still blend orchestration, validation, reporting, or agent behavior.

That is why the internal-review bucket is larger than the clear domain bucket. The useful next step is to narrow mixed modules until each one can be defended as either canonical runtime behavior or lower-layer ownership.
