---
title: Agentic Compatibility Inventory
audience: maintainer
type: reference
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-05-05
---

# agentic-proteins Compatibility Inventory

`agentic-proteins` remains in this repository as an explicit compatibility family. Its modules are allowed to be wrappers or dead ends only. Any remaining canonical or duplicate logic is release-blocking.

## Current Counts

- total modules: 148
- `canonical`: 0
- `dead`: 0
- `duplicate`: 0
- `wrapper`: 148

## Owner Distribution

- `bijux-proteomics-runtime`: 113
- `bijux-proteomics-intelligence`: 20
- `bijux-proteomics-core`: 12
- `bijux-proteomics-knowledge`: 2
- `agentic-proteins-compat`: 1

## Release Rule

- `wrapper` means the module is only preserving an old import or patch seam while delegating live behavior to a canonical package.
- `dead` means the module no longer carries meaningful behavior and can be removed once callers disappear.
- `canonical` or `duplicate` are not allowed to survive in the compatibility family at release time.

## First Proof Check

- `docs/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-compatibility-inventory.csv`
- `docs/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-compatibility-inventory.md`
- `packages/bijux-proteomics-dev/tests/test_agentic_compatibility_inventory.py`
