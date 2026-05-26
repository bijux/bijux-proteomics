# Contracts

## Public package identity

- Distribution name: `proteomics-intelligence`
- Import root: `proteomics_intelligence`
- Canonical owner package: `bijux-proteomics-intelligence`

## Stable contracts

- the alias import root forwards to the canonical intelligence package
- review and recommendation behavior remain owned upstream
- this package stays a compatibility layer rather than a second intelligence owner

## Change requirements

Intelligence behavior changes belong in `bijux-proteomics-intelligence` first.

Changes here should stay focused on compatibility naming, imports, or packaging.

## Consumer upgrade expectations

- recommendation behavior should continue to match the canonical owner
- import-name or packaging changes should be called out explicitly
- consumers should not need to learn a second intelligence contract

## Change routing signals

- route review or recommendation changes to the canonical owner
- keep short-name compatibility work here when no new behavior is introduced
- escalate if the alias begins to own package-local intelligence semantics

## Validation checkpoints

- alias-package tests should prove import routing remains intact
- docs should continue to name `bijux-proteomics-intelligence` as the owner
- canonical intelligence tests should cover any behavior change

## Review questions

- does the change preserve this package as an alias only
- is the canonical intelligence owner still explicit in docs and behavior
- would consumers get the same result from the canonical package directly

## Explicit non-contracts

- This package does not define scientific memory or runtime policy.
- This package does not define a second recommendation owner.
- This package does not replace the canonical intelligence release surface.
