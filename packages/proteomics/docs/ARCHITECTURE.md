# Architecture

## Package identity

- Distribution name: `proteomics`
- Import root: `proteomics`

## Architectural role

`proteomics` is the short install and import alias for
`bijux-proteomics-core`.

## Design constraints

- short aliases must stay mechanically thin
- canonical ownership stays in `bijux-proteomics-core`
- the short alias must not invent a divergent public surface

## Module topology

- the package root owns alias forwarding only
- `cli.py` and `__main__.py` preserve the short command path

## Canonical tree layout

- Import roots: `proteomics`
- Top-level families: none
- Root modules: `__main__.py`, `cli.py`

## Dependency direction

This package may depend on canonical core surfaces to preserve the short alias
experience.

Canonical product packages must not depend on this alias package.

## Downstream expectations

Consumers should use this package only when they need the short alias name; the
scientific owner remains `bijux-proteomics-core`.

## Extension signals

- add code here only when preserving a documented short-alias entrypoint
- keep new behavior forwarding-only rather than widening alias-local logic
- prefer improving the canonical core surface before changing the alias

## Misplacement signals

- if the change defines scientific meaning or workflow logic, it belongs in
  `bijux-proteomics-core`
- if a helper is only useful to canonical callers, it should live in the
  canonical package
- if the alias stops being explainable as a thin forwarding layer, the tree is
  drifting

## Review questions

- does the change preserve the short alias without creating independent product
  behavior
- would the feature still make sense if callers imported only the canonical
  package
- can the package still be described as a short alias after the change
