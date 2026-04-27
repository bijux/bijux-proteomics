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

## Explicit non-contracts

- This package does not define product decision policy.
- This package does not define runtime orchestration behavior.
- This package does not own evidence, ranking, or lab semantics.
