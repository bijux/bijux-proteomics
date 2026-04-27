# Contracts

## Public package identity

- Distribution name: `bijux-proteomics-dev`
- Import root: `bijux_proteomics_dev`
- Stable entrypoints: `quality`, `security`, `api`, `docs`, `release`, and `tools`

## Stable contracts

Modules in this package must be deterministic for the same repository state and
must return non-zero exit codes on contract violations.

Any check used by root `make` targets must emit actionable error text.

For repository API contracts, `bijux-proteomics-dev` enforces that every
`apis/<package>/v1/schema.yaml` has matching `pinned_openapi.json` and
`schema.hash` files and no unversioned breaking field removals.

## Change requirements

Any new repository gate should land with focused tests that pin both the happy
path and the actionable failure message it emits.

## Explicit non-contracts

- This package does not publish runtime product behavior.
- This package does not define proteomics domain truth.
- This package does not override package-owned scientific contracts.
