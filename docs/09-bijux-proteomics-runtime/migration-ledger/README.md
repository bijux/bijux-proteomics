# agentic-proteins Migration Ledger

This ledger classifies every module in `agentic-proteins` to support the
runtime migration plan.

## Classification buckets

- `runtime_execution_ownership`
- `runtime_support_internal_review`
- `domain_ownership`

## Required fields per module

- module path
- classification bucket
- target owner package
- migration reason

## Sources of truth

- rules: `configs/runtime-boundaries/migration-ledger/rules.toml`
- generated ledger: `docs/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-module-ledger.csv`
- generated summary: `docs/09-bijux-proteomics-runtime/migration-ledger/agentic-proteins-module-ledger-summary.md`


## Commands

- `make quality-runtime-migration-ledger` validates ledger freshness and coverage.
- `PYTHONPATH=packages/bijux-proteomics-dev/src python3 -m bijux_proteomics_dev.quality.architecture.runtime_migration_ledger` regenerates ledger outputs.

## Review expectations

When module ownership changes:

1. update `configs/runtime-boundaries/migration-ledger/rules.toml`
2. regenerate ledger outputs
3. run `make quality-runtime-migration-ledger`
4. include rationale updates in the same pull request
