# Contracts

## Public package identity

- Distribution name: `proteomics`
- Import root: `proteomics`
- Canonical owner package: `bijux-proteomics-core`

## Stable contracts

- the short-name alias keeps forwarding to the canonical core owner
- the `proteomics` import root remains a compatibility surface over core
- this package stays a naming alias instead of a second scientific owner

## Change requirements

Core behavior changes belong in `bijux-proteomics-core` first.

Changes here should stay focused on compatibility naming, packaging, or routing
language.

## Consumer upgrade expectations

- scientific behavior should continue to match the canonical core owner
- import-name or command-name changes should be called out explicitly
- consumers should not need to reason about a second owner for core semantics

## Change routing signals

- route scientific logic changes to `bijux-proteomics-core`
- keep short-name compatibility work here when no new behavior is introduced
- escalate if the alias begins to own package-local semantics

## Validation checkpoints

- alias-package tests should prove short-name import routing remains intact
- docs should continue to name `bijux-proteomics-core` as the owner
- canonical core tests should cover any user-visible scientific behavior change

## Review questions

- does the change preserve this package as an alias only
- is the canonical core owner still explicit in docs and behavior
- would consumers get the same result by importing the canonical package

## Explicit non-contracts

- This package does not define scientific semantics.
- This package does not define runtime or recommendation policy.
- This package does not replace the canonical core release surface.
