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

## Extension signals

- add code here when a new concern changes canonical lifecycle meaning, review
  gate behavior, or runtime-agnostic execution protocols
- extend `program_spec.py`, `validation.py`, or `repositories.py` before higher
  packages recreate lifecycle rules locally
- keep new domain invariants here when they define program truth rather than a
  package-specific execution policy

## Misplacement signals

- if the change needs evidence trust, candidate ranking, lab scheduling, or
  operator transport wiring, it belongs in a different package
- if a helper mainly reshapes core state for CLI, API, or replay surfaces, it
  belongs in runtime adapters rather than core models
- if the rule only exists to support one higher-layer recommendation workflow,
  keep it with that owner instead of making core absorb it
