# Contracts

## Public package identity

- Distribution name: `bijux-proteomics-knowledge`
- Import root: `bijux_proteomics_knowledge`
- Stable entrypoints: `memory.models.evidence`, `memory.models.claims`, `memory.reconciliation.resolution`, `reviews.packets`, `contracts.schema`, and `references`

## Stable contracts

- evidence bundles are schema-versioned and serializable
- conflict and resolution records are explicit and auditable
- claim belief updates are derived from typed resolution actions
- curated workflow references stay cited, selective, and machine-readable
- graph validation reports structural issues with stable issue codes

## Change requirements

Behavioral contract changes should always be reflected in tests.

Contract changes should update the focused package tests that pin memory
integrity, resolution semantics, schema compatibility, curated reference
behavior, or graph diagnostics.

## Consumer upgrade expectations

- downstream callers should be able to adopt routine releases without
  rebuilding evidence bundle, claim, resolution, or curated reference parsing
  logic
- intentional contract changes should preserve explicit issue codes and schema
  version anchors instead of relying on implicit interpretation
- consumers should expect conflict, review, and curated reference records to
  remain auditable and machine-readable

## Change routing signals

- evidence bundles, claims, contradiction handling, curated workflow references,
  and graph review contracts belong here first
- execution orchestration, route shaping, ranking or recommendation policy, and
  lab execution logic should be routed back to their owning packages instead of
  being hidden inside evidence helpers
- if runtime, intelligence, or compat surfaces need richer evidence summaries,
  the durable change should start here before higher layers reshape the data

## Validation checkpoints

- memory, schema, and resolution tests should keep evidence transitions and
  diagnostics explicit for changed contracts
- reference and review tests should preserve stable issue codes, provenance, and auditable lineage behavior
- contract changes should stay green in focused package tests before runtime,
  intelligence, or compat layers summarize the evidence differently

## Review questions

- does the contract change alter canonical scientific memory, contradiction,
  trust, provenance, or lineage semantics rather than just reshaping another layer's view
- would another package otherwise create a shadow review or trust contract
- can the contract still be justified without claiming execution orchestration, ranking, recommendation, lab, or runtime-transport ownership

## Explicit non-contracts

- This package does not define execution orchestration or runtime replay policy.
- This package does not define route-shaped transport contracts.
- This package does not define ranking or recommendation policy.
- This package does not define laboratory scheduling or rerun logic.
