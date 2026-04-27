# Contracts

## Public package identity

- Distribution name: `bijux-proteomics-foundation`
- Import root: `bijux_proteomics_foundation`
- Stable entrypoints: `schema`, `serialization`, `ids`, and `migrations`

## Stable contracts

- output of canonical serialization must be deterministic for equivalent models
- schema compatibility checks must return explicit compatibility status and
  reasons
- migration helpers must preserve semantic model meaning across versions

## Change requirements

When this package changes, downstream packages should not need behavioral
rewrites unless the schema contract itself intentionally changes.

Contract-affecting changes should update the focused tests that pin canonical
JSON behavior, compatibility semantics, or migration-path guarantees.

## Consumer upgrade expectations

- downstream packages should be able to adopt routine releases without
  rewriting serialization or migration call sites
- any intentional schema or migration break must be called out as an explicit
  contract change instead of being buried inside implementation churn
- consumers should expect deterministic diagnostics when compatibility checks
  fail

## Change routing signals

- changes to canonical document structure, identifiers, or migration paths
  belong here first
- lifecycle, ranking, evidence, and lab-flow semantics should be routed back to
  their owning packages instead of being patched into foundational models
- if a runtime or compat surface needs new schema behavior, the durable change
  should land here before higher layers widen their forwarding or adapters

## Validation checkpoints

- deterministic serialization tests should pin canonical JSON and fingerprint
  stability for equivalent models
- compatibility and migration tests should make schema-version transitions and
  failure diagnostics explicit
- downstream-facing helper changes should keep focused contract tests green
  before higher-layer packages absorb the new primitive behavior

## Review questions

- does the contract change alter shared document primitives rather than a
  higher-layer policy or execution concern
- would downstream packages otherwise need to invent divergent serialization,
  schema, identifier, or migration behavior
- can the contract still be justified without claiming lifecycle, evidence,
  ranking, lab, or runtime ownership here

## Explicit non-contracts

- This package does not define product decision policy.
- This package does not define runtime orchestration behavior.
- This package does not own evidence, ranking, or lab semantics.
