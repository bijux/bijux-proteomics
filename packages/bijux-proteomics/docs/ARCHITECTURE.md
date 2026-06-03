# Architecture

## Package identity

- Distribution name: `bijux-proteomics`
- Import root: `bijux_proteomics_alias`

## Architectural role

`bijux-proteomics` is the install and command alias for
`bijux-proteomics-core`.

## Design constraints

- alias imports must forward directly to canonical core surfaces
- the package must not accumulate scientific, workflow, or runtime-local logic
- alias entrypoints must stay thin and mechanically explainable

## Module topology

- the package root owns alias forwarding only
- no extra owner families live below the alias root

## Canonical tree layout

- Import roots: `bijux_proteomics_alias`
- Top-level families: none
- Root modules: none

## Dependency direction

This package may depend on canonical core surfaces to preserve the supported
install and command name.

Canonical product packages must not depend on this alias package.

## Downstream expectations

Users should treat this package as a compatibility and packaging convenience,
not as an independent owner of proteomics behavior.

## Extension signals

- add code here only when the alias must preserve a supported canonical core
  entrypoint
- keep new behavior forwarding-only instead of widening alias-local ownership
- prefer fixing the canonical package first before adding alias glue

## Misplacement signals

- if the change defines scientific meaning, workflow behavior, or review logic,
  it belongs in `bijux-proteomics-core`
- if a helper mainly serves canonical callers rather than alias continuity, it
  does not belong here
- if the alias starts carrying package-specific product semantics, the tree has
  drifted from its architecture

## Review questions

- does the change preserve a supported alias surface without inventing new core
  behavior locally
- would the same behavior still make sense if only the canonical core package
  remained
- can the package still be described as forwarding-only after this change
