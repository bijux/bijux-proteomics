# Architecture

## Package identity

- Distribution name: `proteomics-foundation`
- Import root: `proteomics_foundation`

## Architectural role

`proteomics-foundation` is the short alias distribution for
`bijux-proteomics-foundation`.

## Design constraints

- alias imports must forward to canonical foundation primitives
- the package must not absorb shared-contract ownership from the canonical
  foundation package
- the short alias must stay mechanically thin

## Module topology

- the package root owns alias forwarding only
- no extra owner families live below the alias root

## Canonical tree layout

- Import roots: `proteomics_foundation`
- Top-level families: none
- Root modules: none

## Dependency direction

This package may depend on canonical foundation surfaces to preserve the short
alias.

Canonical product packages must not depend on this alias package.

## Downstream expectations

Consumers should use this package only when they need the short alias name; the
real owner remains `bijux-proteomics-foundation`.

## Extension signals

- add code here only when preserving a documented alias surface
- keep changes forwarding-only instead of widening alias-local ownership
- prefer evolving the canonical foundation package before touching the alias

## Misplacement signals

- if the change defines serialization, identity, or compatibility primitives,
  it belongs in `bijux-proteomics-foundation`
- if a helper exists only for canonical callers, it should not live here
- if the alias stops being explainable as thin forwarding, the layout has
  drifted

## Review questions

- does the change preserve the short alias without inventing local primitive
  ownership
- would the same behavior still make sense if only the canonical package
  remained
- can the package still be described as alias-only after the change
