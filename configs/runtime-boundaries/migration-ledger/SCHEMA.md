# Migration Ledger Schema

The generated CSV ledger columns are:

1. `module_path`
2. `bucket`
3. `owner_package`
4. `reason`

## Bucket semantics

- `runtime_execution_ownership`: module belongs in canonical runtime package ownership.
- `runtime_support_internal_review`: module appears runtime-adjacent but needs semantic review before final ownership lock.
- `domain_ownership`: module expresses domain semantics and should move to lower canonical packages.
