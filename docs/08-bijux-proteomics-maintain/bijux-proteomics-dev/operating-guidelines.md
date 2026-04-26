---
title: Operating Guidelines
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Operating Guidelines

Maintainer helper code should stay boring in the good sense: explicit, testable, and easier to audit than the process it replaces.

## Guidelines

- encode repository policy in small, named helpers
- keep maintainer automation easier to review than the workflow calling it
- move product-specific logic back to product packages when the boundary blurs

## First Proof Check

- `packages/bijux-proteomics-dev/src/bijux_proteomics_dev/`
- `packages/bijux-proteomics-dev/tests`

