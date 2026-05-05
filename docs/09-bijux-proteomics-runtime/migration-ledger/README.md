---
title: Migration Ledger
audience: maintainer
type: guide
status: canonical
owner: bijux-proteomics-runtime
last_reviewed: 2026-04-26
---

# agentic-proteins Migration Ledger

This ledger is the checked-in review record for moving legacy `agentic-proteins` modules into the canonical proteomics package family. Its job is not to list modules for the sake of listing them. Its job is to make ownership decisions auditable.

## What The Ledger Decides

- whether a legacy module is clearly runtime-owned
- whether a module still needs runtime-internal review because it mixes responsibilities
- whether a module actually belongs to a lower-layer package instead of runtime

## Bucket Meanings

- `runtime_execution_ownership`: the module is part of canonical runtime execution and should live in `bijux-proteomics-runtime`
- `runtime_support_internal_review`: the module looks runtime-adjacent but still mixes concerns enough to require explicit review before final placement
- `domain_ownership`: the module expresses lower-layer meaning and should move to the owning non-runtime package

## Required Fields

- `module_path`: the legacy module under `agentic-proteins`
- `bucket`: the current ownership-confidence bucket
- `owner_package`: the canonical target package
- `reason`: the justification a reviewer should be able to defend in a pull request

## Sources Of Truth

- rules: `configs/runtime-boundaries/migration-ledger/rules.toml`
- generated ledger: `docs/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-module-ledger.csv`
- generated summary: `docs/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-module-ledger-summary.md`
- compatibility inventory: `docs/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-compatibility-inventory.csv`
- compatibility summary: `docs/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-compatibility-inventory.md`

## Regeneration And Validation

- `make quality-runtime-migration-ledger` validates freshness and coverage
- `PYTHONPATH=packages/bijux-proteomics-dev/src python3 -m bijux_proteomics_dev.quality.architecture.runtime_migration_ledger` regenerates the checked-in outputs

## Review Rules

1. Update `configs/runtime-boundaries/migration-ledger/rules.toml` when ownership reasoning changes.
2. Regenerate the checked-in outputs in the same change.
3. Run `make quality-runtime-migration-ledger` before treating the ledger as current.
4. Explain the ownership change in pull-request language that another maintainer could defend later.
