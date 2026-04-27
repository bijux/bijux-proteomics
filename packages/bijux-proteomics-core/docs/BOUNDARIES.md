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
