---
title: Package Contracts
audience: mixed
type: explanation
status: canonical
owner: bijux-proteomics-dev-docs
last_reviewed: 2026-04-26
---

# Package Contracts

Make fragments encode package contracts too. They show what each package is expected to provide for shared automation.

## Contract Rules

- each package target family should map to a real package capability
- shared automation should not assume hidden package behavior
- when a package differs, document the difference explicitly in its fragment

## First Proof Check

- `makes/packages/agentic-proteins.mk`
- `makes/packages/bijux-proteomics-*.mk`

