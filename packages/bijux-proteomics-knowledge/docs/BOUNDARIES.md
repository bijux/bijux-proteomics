# Boundaries

## Package identity

- Distribution name: `bijux-proteomics-knowledge`
- Import root: `bijux_proteomics_knowledge`

## This package owns

- scientific memory with provenance
- evidence and claim data models
- trust, freshness, and contradiction modeling for stored evidence
- resolution history, evidence graph consistency, and lineage construction
- curated workflow references, ontology mappings, and scientific briefings

## This package does not own

- execution orchestration and runtime replay behavior
- route-shaped payloads, transport-bound views, and operator endpoint shaping
- candidate ranking, recommendation, and selection policies
- laboratory scheduling and outcome rerun policies
- generic uncited context storage

## Dependency direction

This package may depend on foundation primitives and core identifiers while it
stores evidence, claim state, resolution semantics, and curated references for
downstream review.

It should not absorb execution orchestration, route shaping, ranking or
recommendation policy, or lab planning ownership.

## Downstream expectations

Downstream packages should use this package as the canonical source of evidence
memory, provenance, contradiction handling, and lineage semantics instead of
creating local shadow models.

## Escalation signals

- if a change defines evidence trust, contradiction handling, claim lineage, curated workflow caveats, or reviewable provenance meaning, escalate it here before downstream packages fork the model
- if a proposed knowledge helper mainly owns execution orchestration, ranking or recommendation policy, lab execution behavior, or runtime transport, escalate it back to the owning package instead
- if evidence semantics start growing operator-specific payload or orchestration
  rules, treat that as a boundary failure and redesign the seam

## Review questions

- does the change alter canonical scientific memory, contradiction, trust, or lineage semantics rather than just reshaping output for another layer
- would another package create a shadow review or trust model if this behavior stayed out of knowledge
- can the change still be defended without claiming execution orchestration, ranking, recommendation, lab, or runtime transport ownership
