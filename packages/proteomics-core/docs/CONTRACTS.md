# Contracts

## Public package identity

- Distribution name: `proteomics-core`
- Import root: `proteomics_core`
- Canonical owner package: `bijux-proteomics-core`

## Stable contracts

- the alias import root forwards to the canonical core package
- public behavior remains owned by `bijux-proteomics-core`
- this package stays a compatibility layer rather than a second core owner

## Change requirements

Any core behavior change belongs in `bijux-proteomics-core` first.

Changes here should stay focused on compatibility naming, imports, or packaging.

## Consumer upgrade expectations

- scientific behavior should match the canonical core owner
- import-name changes should be called out explicitly
- consumers should not need to learn a second contract for core semantics

## Change routing signals

- route scientific behavior or workflow changes to `bijux-proteomics-core`
- keep compatibility import work here when no new behavior is introduced
- escalate if the alias begins to own package-local semantics

## Validation checkpoints

- alias-package tests should prove import routing remains intact
- docs should continue to name `bijux-proteomics-core` as the owner
- canonical core tests should cover user-visible scientific behavior changes

## Review questions

- does the change preserve this package as an alias only
- is the canonical core owner still explicit in docs and behavior
- would consumers get the same result from the canonical package directly

## Explicit non-contracts

- This package does not define scientific semantics.
- This package does not define runtime or recommendation policy.
- This package does not replace the canonical core release surface.
