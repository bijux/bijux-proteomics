# Boundaries

## Package identity

- Distribution name: `bijux-proteomics-core`
- Import root: `bijux_proteomics`

## This package owns

- program, target, assay, and review entities
- lifecycle transitions and stage eligibility logic
- domain invariants and identifier validations
- runtime adapter interfaces and package CLI entrypoints

## This package does not own

- evidence trust and contradiction resolution
- ranking policy and scenario recommendations
- experiment scheduling and assay rerun policy logic

## Dependency direction

This package may depend on `bijux-proteomics-foundation` for identifiers and
schema primitives, but higher-layer packages should treat this package as the
canonical home for program semantics and gate logic.

This package should not absorb ranking, evidence, lab, or runtime ownership.

## Downstream expectations

Downstream packages should ask core for lifecycle meaning and validation
results instead of re-encoding stage progression rules in local helpers.

## Escalation signals

- if a new rule defines canonical program state, review-gate truth, or stage
  eligibility, escalate it here before higher layers depend on local copies
- if a proposed core change mainly expresses evidence policy, ranking logic,
  lab execution behavior, or runtime transport, escalate it back to the owning
  package instead
- if a lifecycle helper starts depending on CLI, API, replay, or provider
  shapes, treat that as a boundary failure and redesign the seam
