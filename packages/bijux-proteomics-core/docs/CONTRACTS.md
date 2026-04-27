# Contracts

## Public package identity

- Distribution name: `bijux-proteomics-core`
- Import root: `bijux_proteomics`
- Stable entrypoints: `program_spec`, `validation`, `repositories`, and `interfaces`

## Stable contracts

- lifecycle transitions are valid only through declared stage rules
- review gate decisions are deterministic for a given gate state and evidence
- identifier and setup validators produce explicit issue codes
- runtime adapters remain replaceable through protocol contracts

## Change requirements

Downstream packages may consume these contracts, but should not bypass them.

Any contract change should update the package tests that pin stage transitions,
validator diagnostics, or protocol behavior.

## Consumer upgrade expectations

- downstream callers should be able to adopt routine releases without rewriting
  lifecycle orchestration around stage, validation, or repository protocols
- intentional gate or validator behavior changes should be visible through
  stable issue codes and explicit changelog language
- protocol consumers should expect adapters to remain replaceable instead of
  being tied to one runtime or persistence implementation

## Change routing signals

- lifecycle stage law, review gates, and protocol contracts belong here first
- evidence semantics, ranking policy, and lab rerun logic should be routed to
  their owning packages instead of being smuggled into lifecycle helpers
- if runtime needs richer orchestration over lifecycle state, the durable change
  should start here before runtime wraps it with entrypoints or adapters

## Validation checkpoints

- lifecycle and gate tests should make stage transitions and rejection paths
  explicit for the changed contract surface
- validator and protocol tests should preserve stable issue codes and
  replaceable adapter behavior
- contract changes should stay green in focused package tests before runtime or
  higher-layer workflows rely on the new lifecycle semantics

## Explicit non-contracts

- This package does not define evidence trust policy.
- This package does not define ranking or recommendation semantics.
- This package does not define lab scheduling or rerun policy.
