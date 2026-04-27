# Boundaries

## Package identity

- Distribution name: `bijux-proteomics-knowledge`
- Import root: `bijux_proteomics_knowledge`

## This package owns

- evidence and claim data models
- trust and freshness scoring
- contradiction detection and resolution modeling
- evidence graph consistency and lineage construction

## This package does not own

- program review gate ownership
- candidate ranking and selection policies
- laboratory scheduling and outcome rerun policies

## Dependency direction

This package may depend on foundation primitives and core identifiers while it
stores evidence, claim state, and resolution semantics for downstream review.

It should not absorb ranking policy, lifecycle authority, or lab planning
ownership.

## Downstream expectations

Downstream packages should use this package as the canonical source of evidence
trust, contradiction handling, and lineage semantics instead of creating local
shadow models.
