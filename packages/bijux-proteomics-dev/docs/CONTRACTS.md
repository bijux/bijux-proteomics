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

## Consumer upgrade expectations

- maintainers should be able to adopt routine releases without rewriting root
  `make` targets or CI job wiring around the same policy surface
- intentional gate changes should be visible through focused tests and explicit
  failure-message updates instead of silent drift
- callers should expect repository checks to stay deterministic for the same
  checked-in state

## Change routing signals

- repository policy, release validation, docs integrity, and maintainer-only
  automation contracts belong here first
- product runtime behavior and scientific semantics should be routed back to the
  owning package instead of being encoded inside maintainer checks
- if CI or root automation needs a new policy, the durable implementation
  should land here before workflow YAML or ad hoc shell scripts depend on it

## Validation checkpoints

- focused maintainer tests should pin both the happy path and actionable
  failure messages for the changed policy surface
- root `make`, CI-facing, or docs-integrity checks should stay deterministic
  for the same checked-in repository state
- policy changes should stay green in package-level validation before workflow
  YAML or shell wrappers start depending on the new maintainer contract

## Review questions

- does the contract change define repository governance, docs integrity,
  release policy, or maintainer automation rather than product behavior
- would workflow YAML, shell glue, or one-off scripts otherwise become the
  de facto owner of the same policy contract
- can the contract still be justified without claiming runtime execution or
  scientific domain truth as maintainer-owned behavior

## Explicit non-contracts

- This package does not publish runtime product behavior.
- This package does not define proteomics domain truth.
- This package does not override package-owned scientific contracts.
