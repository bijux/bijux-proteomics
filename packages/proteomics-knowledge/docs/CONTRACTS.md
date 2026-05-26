# Contracts

## Public package identity

- Distribution name: `proteomics-knowledge`
- Import root: `proteomics_knowledge`
- Canonical owner package: `bijux-proteomics-knowledge`

## Stable contracts

- the alias import root forwards to the canonical knowledge package
- grounding and curation behavior remain owned upstream
- this package stays a compatibility layer rather than a second knowledge owner

## Change requirements

Knowledge behavior changes belong in `bijux-proteomics-knowledge` first.

Changes here should stay focused on compatibility naming, imports, or
packaging.

## Consumer upgrade expectations

- grounding behavior should continue to match the canonical owner
- import-name or packaging changes should be called out explicitly
- consumers should not need to learn a second knowledge contract

## Change routing signals

- route grounding, curation, or pathway changes to the canonical owner
- keep short-name compatibility work here when no new behavior is introduced
- escalate if the alias begins to own package-local knowledge semantics

## Validation checkpoints

- alias-package tests should prove import routing remains intact
- docs should continue to name `bijux-proteomics-knowledge` as the owner
- canonical knowledge tests should cover any behavior change

## Review questions

- does the change preserve this package as an alias only
- is the canonical knowledge owner still explicit in docs and behavior
- would consumers get the same result from the canonical package directly

## Explicit non-contracts

- This package does not define runtime or recommendation policy.
- This package does not define a second knowledge owner.
- This package does not replace the canonical knowledge release surface.
