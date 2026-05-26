# Contracts

## Public package identity

- Distribution name: `proteomics-foundation`
- Import root: `proteomics_foundation`
- Canonical owner package: `bijux-proteomics-foundation`

## Stable contracts

- the alias import root forwards to the canonical foundation package
- schema, serialization, and compatibility behavior remain owned upstream
- this package stays a compatibility layer rather than a second foundation owner

## Change requirements

Foundation behavior changes belong in `bijux-proteomics-foundation` first.

Changes here should stay focused on compatibility naming, imports, or packaging.

## Consumer upgrade expectations

- kernel behavior should continue to match the canonical foundation owner
- import-name or packaging changes should be called out explicitly
- consumers should not need to learn a second foundation contract

## Change routing signals

- route schema, serialization, or compatibility changes to the canonical owner
- keep short-name compatibility work here when no new behavior is introduced
- escalate if the alias begins to own package-local kernel semantics

## Validation checkpoints

- alias-package tests should prove import routing remains intact
- docs should continue to name `bijux-proteomics-foundation` as the owner
- canonical foundation tests should cover any behavior change

## Review questions

- does the change preserve this package as an alias only
- is the canonical foundation owner still explicit in docs and behavior
- would consumers get the same result from the canonical package directly

## Explicit non-contracts

- This package does not define scientific workflow semantics.
- This package does not define runtime or recommendation policy.
- This package does not replace the canonical foundation release surface.
