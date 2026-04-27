# Tests

## Test scope

`bijux-proteomics-dev` uses pytest tests in `tests/` to prove repository policy,
release gating, docs integrity, and migration governance behavior.

## Required test strata

Each maintenance domain should contribute the narrowest test that proves the
policy it owns:

- parser and policy unit tests for direct rule logic
- command-level tests for maintainers who call package entrypoints through `make`
- contract tests for package docs, workflow structure, and release metadata
- governance tests for runtime migration, compat boundaries, and repository
  policy visibility

## Maintainer expectations

- new repository policy should arrive with a focused test in this package
- tests should emit actionable failures rather than opaque shell noise
- package docs and generated ledgers should be validated by tests before release
- CI should call these tests instead of re-encoding the same policy in workflow
  YAML

## Common validation surfaces

- `test_package_boundary_docs.py`, `test_package_contract_docs.py`, and
  `test_package_architecture_docs.py` protect package documentation contracts
- `test_release_workflows.py` and `test_packaging_contract.py` protect release
  and metadata expectations
- `test_runtime_migration_*` and related boundary tests protect compat-to-runtime
  migration authority
- docs publication and honesty tests protect the public reader-facing contract

## Non-goals

- This page does not replace package-specific scientific or runtime tests.
- This page does not justify policy without executable coverage.
