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

## Consumer upgrade expectations

- downstream callers should be able to adopt routine releases without
  rebuilding evidence bundle, claim, or resolution parsing logic
- intentional contract changes should preserve explicit issue codes and schema
  version anchors instead of relying on implicit interpretation
- consumers should expect conflict and review records to remain auditable and
  machine-readable

## Change routing signals

- evidence bundles, claims, contradiction handling, and graph review contracts
  belong here first
- lifecycle gate authority, ranking policy, and lab execution logic should be
  routed back to their owning packages instead of being hidden inside evidence
  helpers
- if runtime, intelligence, or compat surfaces need richer evidence summaries,
  the durable change should start here before higher layers reshape the data

## Validation checkpoints

- bundle, schema, and resolution tests should keep evidence transitions and
  diagnostics explicit for changed contracts
- graph and review tests should preserve stable issue codes and auditable
  lineage behavior
- contract changes should stay green in focused package tests before runtime,
  intelligence, or compat layers summarize the evidence differently

## Explicit non-contracts

- This package does not define lifecycle gate authority.
- This package does not define ranking or recommendation policy.
- This package does not define laboratory scheduling or rerun logic.
