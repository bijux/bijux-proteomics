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

- total modules: 147
- `canonical`: 0
- `dead`: 1
- `duplicate`: 0
- `wrapper`: 146

## Owner Distribution

- `bijux-proteomics-runtime`: 112
- `bijux-proteomics-intelligence`: 19
- `bijux-proteomics-core`: 15
- `agentic-proteins-compat`: 1

## Forbidden Owner Families

- `bijux-proteomics-foundation`: 0
- `bijux-proteomics-knowledge`: 0
- `bijux-proteomics-lab`: 0

## Release Rule

- `wrapper` means the module is only preserving an old import or patch seam while delegating live behavior to a canonical package.
- `dead` means the module no longer carries meaningful behavior and can be removed once callers disappear.
- `canonical` or `duplicate` are not allowed to survive in the compatibility family at release time.
- foundation, knowledge, and lab ownership are not allowed to survive in the compatibility family at release time.
- direct compat-to-compat import hops remaining: 0
- wrapper modules with local definitions remaining: 0

## First Proof Check

- `docs/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-compatibility-inventory.csv`
- `docs/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-compatibility-inventory.md`
- `packages/bijux-proteomics-dev/tests/quality/architecture/test_agentic_compatibility_inventory.py`
