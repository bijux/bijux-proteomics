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
- `runtime_execution_ownership`: 109
- `runtime_support_internal_review`: 5
- `domain_ownership`: 34

About 74 percent of the ledger is already classified as clear runtime execution ownership, about 3 percent still needs internal review, and about 23 percent is already marked for lower-layer ownership.

## Target Owner Distribution

- `bijux-proteomics-runtime`: 113
- `bijux-proteomics-intelligence`: 19
- `bijux-proteomics-core`: 15
- `agentic-proteins-compat`: 1

## Review Hotspots

- `core/**`: 4 review-required modules
- `__init__.py/**`: 1 review-required modules

## What The Numbers Mean

The main ambiguity is no longer the public runtime surface. The harder work is mixed support code where older modules still blend orchestration, validation, reporting, or agent behavior.

That is why the internal-review bucket is larger than the clear domain bucket. The useful next step is to narrow mixed modules until each one can be defended as either canonical runtime behavior or lower-layer ownership.
