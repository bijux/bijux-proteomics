# Architecture

## Package identity

- Distribution name: `proteomics-runtime`
- Import root: `proteomics_runtime`

## Architectural role

`proteomics-runtime` is the short alias distribution for
`bijux-proteomics-runtime`.

## Design constraints

- short runtime aliases must forward directly to canonical runtime surfaces
- the package must not own orchestration semantics independently
- short CLI and module entrypoints must stay compatibility-thin

## Module topology

- the package root owns alias forwarding only
- `cli.py` and `__main__.py` preserve the short runtime command path

## Canonical tree layout

- Import roots: `proteomics_runtime`
- Top-level families: none
- Root modules: `__main__.py`, `cli.py`

## Dependency direction

This package may depend on canonical runtime surfaces to preserve the short
alias.

Canonical product packages must not depend on this alias package.

## Downstream expectations

Consumers should use this package only when they need the short runtime alias;
the real execution owner remains `bijux-proteomics-runtime`.

## Extension signals

- add code here only when preserving a documented short runtime alias surface
- keep changes forwarding-only rather than widening alias-local orchestration
- prefer evolving the canonical runtime package before touching the alias

## Misplacement signals

- if the change defines workflow execution, replay, or provider behavior, it
  belongs in `bijux-proteomics-runtime`
- if a helper exists only for canonical runtime callers, it should not live
  here
- if the alias stops being explainable as thin forwarding, the layout has
  drifted

## Review questions

- does the change preserve the short runtime alias without inventing local
  orchestration behavior
- would the same feature still make sense if the canonical runtime package were
  the only implementation
- can the package still be described as alias-only after the change
