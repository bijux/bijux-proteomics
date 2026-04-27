# Architecture

## Package identity

- Distribution name: `bijux-proteomics-foundation`
- Import root: `bijux_proteomics_foundation`

## Architectural role

`bijux-proteomics-foundation` exists to centralize shared document primitives so
every higher-level package can serialize, fingerprint, and version its models
with the same rules.

## Design constraints

- schema metadata is explicit and model-attached
- canonical serialization is deterministic across runs
- compatibility checks are data-model aware, not file-path aware

## Module topology

- `schema.py` owns versioned schema identity and compatibility status
- `serialization.py` owns canonical JSON and fingerprint behavior
- `migrations.py` owns declarative version-to-version upgrade flow
- `ids.py` owns stable identifier kinds and construction helpers
- `errors.py` owns shared contract and migration error primitives

## Dependency direction

This package is intentionally dependency-light and stable so upstream packages
can rely on it as a low-volatility contract surface.

Higher-level packages may depend on these primitives, but this package should
not absorb runtime orchestration or scientific policy semantics from those
layers.

## Downstream expectations

Downstream packages should compose these primitives instead of rebuilding
serialization rules, compatibility logic, or migration path behavior locally.

## Extension signals

- add code here when a new concern changes canonical document primitives shared
  by multiple packages
- extend `schema.py`, `serialization.py`, `ids.py`, or `migrations.py` before
  higher packages invent local copies of the same rules
- prefer adding stable low-volatility helpers here when the change would
  otherwise fragment serialization or compatibility behavior across packages

## Misplacement signals

- if the change needs lifecycle authority, recommendation policy, evidence
  semantics, lab scheduling, or operator entrypoints, it belongs in a higher
  package
- if the change mostly reshapes runtime transport or orchestration payloads, it
  belongs in `bijux-proteomics-runtime` adapters rather than here
- if a package-specific helper would only be used by one domain layer, keep it
  with that owner instead of forcing it into shared primitives
