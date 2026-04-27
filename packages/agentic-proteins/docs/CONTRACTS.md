# Contracts

## Public package identity

- Distribution name: `agentic-proteins`
- Import root: `agentic_proteins`
- Legacy CLI command: `agentic-proteins`
- Canonical replacement package: `bijux-proteomics-runtime`

## Stable contracts

- forwarding keeps legacy imports available while canonical packages own behavior
- CLI and API compatibility surfaces mirror canonical runtime contracts
- compat documentation names the canonical package that now owns each surface

## Change requirements

Behavioral changes in canonical runtime execution must be reflected by tests and
artifact expectations before compat forwarding is widened or rewritten.

Compat-specific changes should update the forwarding and boundary tests that
guard strict compat mode.

## Consumer upgrade expectations

- downstream users should be able to keep legacy imports and CLI entrypoints
  working while they migrate toward canonical package roots
- intentional compat-routing changes should be visible through forwarding tests
  and explicit canonical-owner documentation updates
- consumers should expect compat releases to mirror canonical ownership rather
  than introduce new behavior of their own

## Change routing signals

- legacy import forwarding, compat CLI routing, and migration-safe package
  identity belong here first
- canonical runtime and lower-layer domain behavior should be routed to their
  owning packages instead of being reimplemented in compat shims
- if users need a new legacy surface, the durable canonical contract change
  should land in the owning package before compat exposes a forwarding alias

## Explicit non-contracts

- This package is not the canonical runtime.
- This package is not a place for new domain logic.
- This package does not define a permanent deprecation policy by itself.
