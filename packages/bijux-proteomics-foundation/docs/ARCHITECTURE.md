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

- `serialization/documents.py` owns document metadata and shared value wrappers
- `compatibility/evolution.py`, `compatibility/migrations.py`, and
  `compatibility/versions.py` own schema compatibility and version-to-version
  upgrade flow
- `serialization/canonicalization.py`, `serialization/hashing.py`,
  `serialization/fingerprints.py`, `serialization/json_models.py`, and
  `serialization/ordering.py` own deterministic rendering, hashing, and
  fingerprint behavior
- `identity/identifiers.py` owns stable identifier kinds and construction helpers
- `support/provenance.py`, `support/states.py`, and `support/charter.py` own
  shared provenance, support-state, and package-charter contracts
- `outcomes/exceptions.py`, `outcomes/error_envelopes.py`,
  `outcomes/refusals.py`, and `outcomes/results.py` own shared
  machine-readable contract outcomes

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
- extend `serialization/documents.py`, `compatibility/evolution.py`,
  `serialization/canonicalization.py`, `serialization/hashing.py`,
  `identity/identifiers.py`, or `compatibility/migrations.py` before
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

## Review questions

- does the change define a shared document primitive that at least two package
  layers should rely on directly
- would leaving the change out of foundation force higher packages to invent
  incompatible serialization, identifier, or migration behavior
- can the architecture still be explained without claiming any lifecycle,
  ranking, evidence, lab, or runtime semantics here
