# Architecture

## Package identity

- Distribution name: `proteomics-intelligence`
- Import root: `proteomics_intelligence`

## Architectural role

`proteomics-intelligence` is the short alias distribution for
`bijux-proteomics-intelligence`.

## Design constraints

- the short alias must forward to canonical intelligence ownership
- the package must not own independent review or recommendation policy
- alias imports must stay mechanically thin

## Module topology

- the package root owns alias forwarding only
- no extra owner families live below the alias root

## Canonical tree layout

- Import roots: `proteomics_intelligence`
- Top-level families: none
- Root modules: none

## Dependency direction

This package may depend on canonical intelligence surfaces to preserve the
short alias.

Canonical product packages must not depend on this alias package.

## Downstream expectations

Consumers should use this package only when they need the short alias name; the
real owner remains `bijux-proteomics-intelligence`.

## Extension signals

- add code here only when preserving a documented alias surface
- keep changes forwarding-only instead of widening alias-local review logic
- prefer evolving the canonical intelligence package before touching the alias

## Misplacement signals

- if the change defines recommendation, refusal, or review semantics, it
  belongs in `bijux-proteomics-intelligence`
- if a helper exists only for canonical callers, it should not live here
- if the alias stops being explainable as thin forwarding, the layout has
  drifted

## Review questions

- does the change preserve the short alias without inventing local review
  behavior
- would the same behavior still make sense if only the canonical package
  remained
- can the package still be described as alias-only after the change
