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

- `domain/` owns canonical program semantics: targets, constraints, context,
  criteria, liabilities, lifecycle, review gates, and validation
- `io/` owns normalized format, spectrum, and serialization boundaries
- `workflow/` owns scientific workflow blueprints and runtime manifests
- `execution/` owns runtime-agnostic execution contracts and adapter seams
- root-level modules remain as compatibility import shims while the package
  surface is normalized around intent-based subpackages
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
- extend `domain/program_spec.py`, `domain/validation.py`, or `domain/repositories.py` before higher
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

## Review questions

- does the change alter canonical lifecycle meaning, review gates, or
  runtime-agnostic execution protocols
- would higher packages become the de facto source of truth for progression
  rules if this behavior stayed out of core
- can the architecture still be described without relying on runtime transport,
  evidence semantics, or lab-local workflow exceptions
