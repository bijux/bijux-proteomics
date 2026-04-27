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

## Explicit non-contracts

- This package does not define lifecycle gate authority.
- This package does not define ranking or recommendation policy.
- This package does not define evidence trust or contradiction semantics.
