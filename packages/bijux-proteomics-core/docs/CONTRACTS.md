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

## Explicit non-contracts

- This package does not define evidence trust policy.
- This package does not define ranking or recommendation semantics.
- This package does not define lab scheduling or rerun policy.
