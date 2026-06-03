# Contracts

## Public package identity

- Distribution name: `proteomics-lab`
- Import root: `proteomics_lab`
- Canonical owner package: `bijux-proteomics-lab`

## Stable contracts

- the alias import root forwards to the canonical lab package
- assay-planning and handoff behavior remain owned upstream
- this package stays a compatibility layer rather than a second lab owner

## Change requirements

Lab behavior changes belong in `bijux-proteomics-lab` first.

Changes here should stay focused on compatibility naming, imports, or
packaging.

## Consumer upgrade expectations

- lab behavior should continue to match the canonical owner
- import-name or packaging changes should be called out explicitly
- consumers should not need to learn a second lab contract

## Change routing signals

- route assay-planning or handoff changes to the canonical owner
- keep short-name compatibility work here when no new behavior is introduced
- escalate if the alias begins to own package-local lab semantics

## Validation checkpoints

- alias-package tests should prove import routing remains intact
- docs should continue to name `bijux-proteomics-lab` as the owner
- canonical lab tests should cover any behavior change

## Review questions

- does the change preserve this package as an alias only
- is the canonical lab owner still explicit in docs and behavior
- would consumers get the same result from the canonical package directly

## Explicit non-contracts

- This package does not define scientific core semantics.
- This package does not define a second lab owner.
- This package does not replace the canonical lab release surface.
