# Contracts

## Public package identity

- Distribution name: `bijux-proteomics`
- Public import root: `bijux_proteomics`
- Private metadata helper: `bijux_proteomics_alias`
- Canonical owner package: `bijux-proteomics-core`

## Stable contracts

- the distribution name continues to install the canonical core owner
- the public scientific import surface remains `bijux_proteomics`
- the local `bijux_proteomics_alias` helper remains version metadata only
- this package stays a naming alias rather than a second scientific owner

## Change requirements

Any behavior change must land in `bijux-proteomics-core` first.

Alias changes should be limited to packaging, naming, or clearly documented
compatibility routing.

## Consumer upgrade expectations

- downstream scientific behavior should match the canonical core owner
- install-name or dependency changes should be called out explicitly
- consumers should not need to learn a second owner contract for core logic

## Change routing signals

- route scientific behavior changes to `bijux-proteomics-core`
- keep distribution-name compatibility work here when no new behavior is added
- stop and escalate if the alias starts acquiring package-local semantics

## Validation checkpoints

- alias-package tests should prove install-name routing remains intact
- docs should continue to name `bijux-proteomics-core` as the owner
- canonical core tests should cover any user-visible behavior change

## Review questions

- does the change preserve this package as an alias only
- is the canonical core owner still explicit in docs and behavior
- would the same result hold if consumers used the canonical package directly

## Explicit non-contracts

- This package does not define scientific semantics.
- This package does not define runtime or recommendation policy.
- This package does not replace the canonical core release surface.
