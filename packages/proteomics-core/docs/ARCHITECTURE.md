# Architecture

## Package identity

- Distribution name: `proteomics-core`
- Import root: `proteomics_core`

## Architectural role

`proteomics-core` is the short alias distribution for
`bijux-proteomics-core`.

## Design constraints

- the alias must forward to canonical core ownership instead of shadowing it
- short command and import paths stay available without redefining behavior
- alias-local modules must remain compatibility-only

## Module topology

- the package root owns alias forwarding only
- `cli.py` and `__main__.py` preserve the short CLI entrypoint

## Canonical tree layout

- Import roots: `proteomics_core`
- Top-level families: none
- Root modules: `__main__.py`, `cli.py`

## Dependency direction

This package may depend on canonical core surfaces to preserve the short alias
experience.

Canonical product packages must not depend on this alias package.

## Downstream expectations

Callers should treat this package as a compatibility alias, not as an
independent owner of core proteomics behavior.

## Extension signals

- add code here only when preserving a documented short-alias surface
- keep alias behavior forwarding-only instead of widening local ownership
- prefer fixing the canonical core package before touching the alias

## Misplacement signals

- if the change defines scientific or workflow semantics, it belongs in
  `bijux-proteomics-core`
- if a helper exists for canonical callers only, it does not belong in the
  alias package
- if the alias becomes harder to explain as thin forwarding, the layout has
  drifted

## Review questions

- does the change preserve the short alias without inventing local product
  behavior
- would the same surface still make sense if the canonical package were the
  only implementation
- can the package still be described as alias-only after the change
