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
