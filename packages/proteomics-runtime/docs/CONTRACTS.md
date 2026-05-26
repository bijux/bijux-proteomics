# Contracts

## Public package identity

- Distribution name: `proteomics-runtime`
- Import root: `proteomics_runtime`
- Canonical owner package: `bijux-proteomics-runtime`

## Stable contracts

- the alias import root forwards to the canonical runtime package
- execution behavior remains owned by `bijux-proteomics-runtime`
- this package stays a compatibility layer rather than a second runtime owner

## Change requirements

Runtime behavior changes belong in `bijux-proteomics-runtime` first.

Changes here should stay focused on compatibility naming, imports, CLI routing,
or packaging.

## Consumer upgrade expectations

- execution behavior should continue to match the canonical runtime owner
- import-name or command-name changes should be called out explicitly
- consumers should not need to learn a second runtime contract

## Change routing signals

- route provider, workflow, or execution behavior changes to the canonical owner
- keep short-name compatibility work here when no new behavior is introduced
- escalate if the alias begins to own package-local runtime semantics

## Validation checkpoints

- alias-package tests should prove import and CLI routing remain intact
- docs should continue to name `bijux-proteomics-runtime` as the owner
- canonical runtime tests should cover any behavior change

## Review questions

- does the change preserve this package as an alias only
- is the canonical runtime owner still explicit in docs and behavior
- would consumers get the same result from the canonical package directly

## Explicit non-contracts

- This package does not define scientific semantics.
- This package does not define a second runtime owner.
- This package does not replace the canonical runtime release surface.
