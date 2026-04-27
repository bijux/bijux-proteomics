# Contracts

## Public package identity

- Distribution name: `bijux-proteomics-lab`
- Import root: `bijux_proteomics_lab`
- Stable entrypoints: `planning`, `outcomes`, `repositories`, `schema`, and `serialization`

## Stable contracts

- planning outputs include explicit dependency and gating context
- outcome summaries expose failure class and rerun guidance fields
- repository abstractions remain storage-agnostic and typed

## Change requirements

Any change to planning or triage semantics should include corresponding test
updates.

Contract changes should update the focused package tests that pin planning,
outcome interpretation, schema compatibility, or serialization behavior.

## Consumer upgrade expectations

- downstream callers should be able to adopt routine releases without rewriting
  planning, outcome, or repository integration logic
- intentional planning or rerun changes should be visible through explicit
  schema, outcome, and changelog updates
- consumers should expect outcome summaries to stay typed and actionable rather
  than becoming free-form operator notes

## Change routing signals

- planning contracts, outcome summaries, and lab repository abstractions belong
  here first
- lifecycle gate law, evidence truth, and ranking policy should be routed back
  to their owning packages instead of being folded into lab orchestration
- if runtime or compat surfaces need richer operator workflows, the durable
  planning or outcome contract change should start here before higher layers
  expose it through entrypoints

## Validation checkpoints

- planning and dependency tests should make schedule, batching, and gating
  changes explicit for the edited contract surface
- outcome and repository tests should preserve typed rerun guidance and
  storage-agnostic abstractions
- contract changes should stay green in focused package tests before runtime or
  compat layers widen operator workflows around the new lab behavior

## Explicit non-contracts

- This package does not define lifecycle gate authority.
- This package does not define ranking or recommendation policy.
- This package does not define evidence trust or contradiction semantics.
