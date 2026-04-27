# Architecture

## Package identity

- Distribution name: `bijux-proteomics-core`
- Import root: `bijux_proteomics`

## Architectural role

`bijux-proteomics-core` models the program-centric domain: targets, constraints,
assays, review gates, lifecycle transitions, and execution adapter protocols.

## Design constraints

- domain entities are explicit and strongly typed
- review and lifecycle rules are model-level invariants
- execution integration stays behind protocol boundaries

## Module topology

- `program_spec.py` owns primary lifecycle entities and stage semantics
- `validation.py` owns invariant checks and issue reporting
- `repositories.py` owns storage-agnostic repository protocols
- `interfaces/` owns operator-facing package CLI boundaries

## Dependency direction

The package is designed as the durable semantic source of truth for progression
and review behavior.

Higher layers may depend on this package for canonical program meaning, but
this package should not absorb evidence trust, ranking policy, or laboratory
execution semantics.

## Downstream expectations

Downstream packages should use these models and validators instead of
recreating lifecycle logic in runtime, intelligence, or lab-specific helpers.
