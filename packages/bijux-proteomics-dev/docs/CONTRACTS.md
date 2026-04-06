# Contracts

Modules in this package must be deterministic for the same repository state and
must return non-zero exit codes on contract violations.

Any check used by root `make` targets must emit actionable error text.

For repository API contracts, `bijux-proteomics-dev` enforces that every
`apis/<package>/v1/schema.yaml` has matching `pinned_openapi.json` and
`schema.hash` files and no unversioned breaking field removals.
