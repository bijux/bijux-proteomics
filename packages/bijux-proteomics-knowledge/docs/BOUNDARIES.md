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

## Escalation signals

- if a change defines evidence trust, contradiction handling, claim lineage, or
  reviewable provenance meaning, escalate it here before downstream packages
  fork the model
- if a proposed knowledge helper mainly owns lifecycle authority, ranking
  policy, lab execution behavior, or runtime transport, escalate it back to the
  owning package instead
- if evidence semantics start growing operator-specific payload or orchestration
  rules, treat that as a boundary failure and redesign the seam
