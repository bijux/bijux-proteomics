# Contracts

## Public package identity

- Distribution name: `bijux-proteomics-knowledge`
- Import root: `bijux_proteomics_knowledge`
- Stable entrypoints: `evidence`, `claims`, `resolution`, `graph`, and `review`

## Stable contracts

- evidence bundles are schema-versioned and serializable
- conflict and resolution records are explicit and auditable
- claim belief updates are derived from typed resolution actions
- graph validation reports structural issues with stable issue codes

## Change requirements

Behavioral contract changes should always be reflected in tests.

Contract changes should update the focused package tests that pin bundle
integrity, resolution semantics, schema compatibility, or graph diagnostics.

## Explicit non-contracts

- This package does not define lifecycle gate authority.
- This package does not define ranking or recommendation policy.
- This package does not define laboratory scheduling or rerun logic.
